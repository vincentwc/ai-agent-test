import os
from typing import Annotated

import alibabacloud_bailian20231229.client as bailian_20231229_client
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


@mcp.tool(name="query_rag",description="从阿里云百炼知识库中读取知识信息")
def query_rag_from_bailian(
        query: Annotated[str, Field(description="访问知识库查询的内容", examples=["终端的操作规范"])]) -> str:
    bailian_client = create_client()
    workspace_id = "llm-c3naymmpo4uc2ur0"
    index_id = "ygav25j8sf"
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


if __name__ == '__main__':
    mcp.run(transport="stdio")
    # bailian_client = create_client()
    #
    # workspace_id = "llm-c3naymmpo4uc2ur0"
    # index_id = "ygav25j8sf"
    #
    # rag = retrieve_index(bailian_client, workspace_id, index_id, "终端操作规范")
    # print(rag.body.data.nodes[0].text)
