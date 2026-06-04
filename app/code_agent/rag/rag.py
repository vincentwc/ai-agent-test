import os
import hashlib
from typing import Annotated

import alibabacloud_bailian20231229.client as bailian_20231229_client
import requests
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_bailian20231229 import models as bailian_20231229_models
from alibabacloud_tea_util import models as util_models
from dotenv import load_dotenv
from pydantic import Field
from mcp.server.fastmcp import FastMCP

mcp = FastMCP()

load_dotenv()

ALIBABA_CLOUD_ACCESS_KEY_ID = os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID")
ALIBABA_CLOUD_ACCESS_KEY_SECRET = os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_SECRET")


def create_client() -> bailian_20231229_client.Client:
    config = open_api_models.Config(
        access_key_id=ALIBABA_CLOUD_ACCESS_KEY_ID,
        access_key_secret=ALIBABA_CLOUD_ACCESS_KEY_SECRET
    )

    # 下方接入地址以公有云的公网接入地址为例，可按需更换接入地址。
    config.endpoint = 'bailian.cn-beijing.aliyuncs.com'
    return bailian_20231229_client.Client(config)


def retrieve_index(client, workspace_id: str, index_id: str, query: str):
    """
    从阿里云百炼知识库中读取知识
    :param client: 百炼客户端
    :param workspace_id: 工作空间ID
    :param index_id: 知识库ID
    :param query: 查询语句
    :return: 知识库查询结果
    """
    retrieve_request = bailian_20231229_models.RetrieveRequest(
        index_id=index_id,
        query=query,
    )
    runtime = util_models.RuntimeOptions()
    return client.retrieve_with_options(
        workspace_id,
        retrieve_request,
        {},
        runtime,
    )


@mcp.tool(name="query_rag", description="从阿里云百炼知识库中读取知识信息")
def query_rag_from_bailian(
        query: Annotated[str, Field(description="访问知识库查询的内容", examples=["终端的操作规范"])]) -> str:
    bailian_client = create_client()
    workspace_id = "llm-c3naymmpo4uc2ur0"
    index_id = "w25cj65i8n"
    rag = retrieve_index(bailian_client, workspace_id, index_id, query)

    result = ""

    for data in rag.body.data.nodes:
        result += f"""{data.text}
___"""

    print("-" * 60)
    print("[query_rag_from_bailian]", query)
    print(result)
    print("-" * 60)
    return result


def apply_lease(client, category_id, file_name, file_md5, file_size, workspace_id):
    headers = {}
    runtime = util_models.RuntimeOptions()
    request = bailian_20231229_models.ApplyFileUploadLeaseRequest(
        file_name=file_name,
        md_5=file_md5,
        size_in_bytes=file_size,
    )
    return client.apply_file_upload_lease_with_options(
        category_id,
        workspace_id,
        request,
        headers,
        runtime,
    )


def calculate_md5(file_path: str) -> str:
    """
    计算文件的 MD5 哈希值。

    参数:
        file_path (str): 文件路径。

    返回:
        str: 文件的 MD5 哈希值。
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_file_info(file_path):
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    file_md5 = calculate_md5(file_path)
    return file_name, file_size, file_md5


def apply_lease_by_file(client, category_id, workspace_id, file_path):
    file_name, file_size, file_md5 = get_file_info(file_path)

    return apply_lease(client, category_id, file_name, file_md5, file_size, workspace_id)


def upload_file_to_bailian(upload_url, headers, file_path):
    with open(file_path, "rb") as f:
        file_content = f.read()

    upload_headers = {
        "Content-Type": headers["Content-Type"],
        "X-bailian-extra": headers["X-bailian-extra"],
    }
    response = requests.put(
        upload_url,
        data=file_content,
        headers=upload_headers,
    )
    response.raise_for_status()


def add_file_to_bailian_category(client, lease_id, parser, category_id, workspace_id):
    headers = {}
    runtime = util_models.RuntimeOptions()
    request = bailian_20231229_models.AddFileRequest(
        lease_id=lease_id,
        parser=parser,
        category_id=category_id,
    )

    return client.add_file_with_options(
        workspace_id,
        request,
        headers,
        runtime,
    )


def describe_file(client, workspace_id, file_id):
    headers = {}
    runtime = util_models.RuntimeOptions()

    return client.describe_file_with_options(
        workspace_id,
        file_id,
        headers,
        runtime,
    )


def upload_rag_file_to_bailian(client, workspace_id, category_id, file_path):
    """
    上传文件到百炼数据中心，并添加到指定分类

    参数：
        client: 百炼客户端
        workspace_id: 业务空间ID
        category_id: 分类ID
        file_path: 文件路径

    返回：
        文件上传状态
    """

    print("=" * 100)
    # 1. 申请文件租约
    lease = apply_lease_by_file(client, category_id, workspace_id, file_path)
    headers = lease.body.data.param.headers
    lease_id = lease.body.data.file_upload_lease_id
    upload_url = lease.body.data.param.url
    print("-" * 60)
    print("文件租约申请成功")
    print("headers:", headers)
    print("lease_id:", lease_id)
    print("upload_url:", upload_url)
    print("-" * 60)
    print()

    # 2. 上传文件到百炼数据中心
    upload_file_to_bailian(upload_url, headers, file_path)

    # 3. 添加文件到指定分类
    add_file_response = add_file_to_bailian_category(
        client,
        lease_id,
        "DASHSCOPE_DOCMIND",
        category_id,
        workspace_id
    )
    rag_file_id = add_file_response.body.data.file_id
    print("-" * 60)
    print("添加分类成功")
    print("rag_file_id:", rag_file_id)
    print("-" * 60)
    print()

    # 4. 获取文件上传状态
    describe_file_response = describe_file(client, workspace_id, rag_file_id)
    print("-" * 60)
    print("获取文件状态成功")
    print("describe_file_response:", describe_file_response.body)
    print("-" * 60)
    print("=" * 100)

    return describe_file_response


if __name__ == '__main__':
    # mcp.run(transport="stdio")
    rag_file_path = "/Users/vincent/developEnv/code/ai/ai-agent-test/app/code_agent/rag/rag_test.txt"
    rag_category_id = "cate_1b43c6643b6541b983800bf8ebc31c9f_12601485"
    rag_workspace_id = "llm-c3naymmpo4uc2ur0"

    bailian_client = create_client()

    # upload_file_to_bailian(upload_url, headers, rag_file_path)

    # add_file_response = add_file_to_bailian_category(bailian_client, lease_id, "DASHSCOPE_DOCMIND", rag_category_id, rag_workspace_id)

    # rag_file_id = add_file_response.body.data.file_id
    # rag_field_id = "file_3aab3e615ab7432ca8c2f0ae5917ff0b_12601485"

    # describe_response = describe_file(bailian_client, rag_workspace_id, rag_field_id)
    # print(describe_response)

    upload_rag_file_to_bailian(
        bailian_client, rag_workspace_id, rag_category_id, rag_file_path)
