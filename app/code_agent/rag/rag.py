import os
import hashlib
from email import header
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


# @mcp.tool(name="query_rag", description="从阿里云百炼知识库中读取知识信息")
# def query_rag_from_bailian(
#         query: Annotated[str, Field(description="访问知识库查询的内容", examples=["终端的操作规范"])]) -> str:
#     bailian_client = create_client()
#     workspace_id = "llm-c3naymmpo4uc2ur0"
#     index_id = "w25cj65i8n"
#     rag = retrieve_index(bailian_client, workspace_id, index_id, query)
#
#     result = ""
#
#     for data in rag.body.data.nodes:
#         result += f"""{data.text}
# ___"""
#
#     print("-" * 60)
#     print("[query_rag_from_bailian]", query)
#     print(result)
#     print("-" * 60)
#     return result


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


def create_index(
        client,
        workspace_id,
        name,
        file_id,
        structure_type="unstructured",
        source_type="DATA_CENTER_FILE",
        sink_type="BUILT_IN"
):
    """
    在阿里云百炼服务中创建知识库（初始化）。

    参数:
        client (bailian20231229Client): 客户端（Client）。
        workspace_id (str): 业务空间ID。
        name (str): 知识库名称。
        file_id (str): 文档ID。
        structure_type (str): 知识库的数据类型。
        source_type (str): 应用数据的数据类型，支持类目类型和文档类型。
        sink_type (str): 知识库的向量存储类型。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    request = bailian_20231229_models.CreateIndexRequest(
        structure_type=structure_type,
        name=name,
        source_type=source_type,
        sink_type=sink_type,
        document_ids=[file_id]
    )
    runtime = util_models.RuntimeOptions()
    return client.create_index_with_options(workspace_id, request, headers, runtime)


def submit_index(client, workspace_id, index_id):
    headers = {}
    runtime = util_models.RuntimeOptions()
    submit_index_job_request = bailian_20231229_models.SubmitIndexJobRequest(index_id=index_id)

    return client.submit_index_job_with_options(workspace_id, submit_index_job_request, headers, runtime)


def get_index_job_status(client, workspace_id, index_id, job_id):
    headers = {}
    runtime = util_models.RuntimeOptions()

    get_index_job_status_request = bailian_20231229_models.GetIndexJobStatusRequest(
        index_id=index_id,
        job_id=job_id,
    )
    return client.get_index_job_status_with_options(workspace_id, get_index_job_status_request, headers, runtime)


def list_indices(client, workspace_id):
    """
    获取指定业务空间下一个或多个知识库的详细信息。

    参数:
        client (bailian20231229Client): 客户端（Client）。
        workspace_id (str): 业务空间ID。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    list_indices_request = bailian_20231229_models.ListIndicesRequest()
    runtime = util_models.RuntimeOptions()
    return client.list_indices_with_options(workspace_id, list_indices_request, headers, runtime)


def submit_index_add_documents_job(client, workspace_id, index_id, file_id, source_type="DATA_CENTER_FILE"):
    """
    向一个非结构化知识库追加导入已解析的文档。

    参数:
        client (bailian20231229Client): 客户端（Client）。
        workspace_id (str): 业务空间ID。
        index_id (str): 知识库ID。
        file_id (str): 文档ID。
        source_type(str): 数据类型。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    submit_index_add_documents_job_request = bailian_20231229_models.SubmitIndexAddDocumentsJobRequest(
        index_id=index_id,
        document_ids=[file_id],
        source_type=source_type
    )
    runtime = util_models.RuntimeOptions()
    return client.submit_index_add_documents_job_with_options(workspace_id, submit_index_add_documents_job_request,
                                                              headers, runtime)


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

    return rag_file_id


def add_document_to_index(client, workspace_id, index_id, file_id):
    job_response = submit_index_add_documents_job(client, workspace_id, index_id, file_id)
    job_id = job_response.body.data.id

    job_status = get_index_job_status(client, workspace_id, index_id, job_id)
    print(job_status.body.data)


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

    return result


@mcp.tool(name="upload_local_file_path_to_bailian_rag", description="将本地的知识文件上传到百炼平台知识库")
def upload_rag_to_bailian(file_path: Annotated[
    str,
    Field(
        description="本地的知识文件路径",
        examples="/Users/vincent/developEnv/code/ai/ai-agent-test/app/code_agent/rag/rag_test.txt"
    )]):

    bailian_client = create_client()
    workspace_id = "llm-c3naymmpo4uc2ur0"
    category_id = "cate_1b43c6643b6541b983800bf8ebc31c9f_12601485"
    index_id = "1x5ful2dao"

    field_id = upload_rag_file_to_bailian(bailian_client, workspace_id, category_id, file_path)

    response = add_document_to_index(bailian_client, workspace_id, index_id, field_id)

    return response


@mcp.tool(name="query_bailian_rag_job_status", description="查询上传到百炼知识库中的知识文件处理状态")
def query_bailian_rag_job_status(job_id: str):
    bailian_client = create_client()
    workspace_id = "llm-c3naymmpo4uc2ur0"
    index_id = "1x5ful2dao"

    job_status = get_index_job_status(bailian_client, workspace_id, index_id, job_id)
    return job_status.body.data


if __name__ == '__main__':
    mcp.run(transport="stdio")
    # rag_file_path = "/Users/vincent/developEnv/code/ai/ai-agent-test/app/code_agent/rag/rag_test.txt"
    # rag_category_id = "cate_1b43c6643b6541b983800bf8ebc31c9f_12601485"
    # rag_workspace_id = "llm-c3naymmpo4uc2ur0"

    # bailian_client = create_client()

    # upload_file_to_bailian(upload_url, headers, rag_file_path)

    # add_file_response = add_file_to_bailian_category(bailian_client, lease_id, "DASHSCOPE_DOCMIND", rag_category_id, rag_workspace_id)

    # rag_file_id = add_file_response.body.data.file_id
    # rag_field_id = "file_3aab3e615ab7432ca8c2f0ae5917ff0b_12601485"

    # describe_response = describe_file(bailian_client, rag_workspace_id, rag_field_id)
    # print(describe_response)

    # upload_rag_file_to_bailian(bailian_client, rag_workspace_id, rag_category_id, rag_file_path)

    # response = create_index(bailian_client, rag_workspace_id, "智能体控制知识库", "file_3aab3e615ab7432ca8c2f0ae5917ff0b_12601485")
    # print(response)

    # index_id = "1x5ful2dao"
    # job_response = submit_index(bailian_client, rag_workspace_id, index_id)
    # print(job_response)

    # job_id = job_response.body.data.id
    # print("job_id:", job_id)

    # rag_job_id = "e49ee5e990514686adb97692696e85f9"
    # job_status_response = get_index_job_status(bailian_client, rag_workspace_id, index_id, rag_job_id)
    # print(job_status_response.body.data)

    # list_indices_response = list_indices(bailian_client, rag_workspace_id)
    # print(list_indices_response.body.data)

    # rag_file_id = "file_2496c48b0aff4e49b6b925d78edf239e_12601485"
    # response = submit_index_add_documents_job(bailian_client, rag_workspace_id, index_id, rag_file_id)
    # print(response)

    # rag_job_id = "a009a29388b24f83b11f611a7fd6fa4d"
    # job_status_response = get_index_job_status(bailian_client, rag_workspace_id, index_id, rag_job_id)
    # print(job_status_response.body.data)
