import os

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()  # 自动读取 .env 文件
llm_qwen = ChatOpenAI(
    model= "qwen-max",
    base_url= "https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key= os.environ.get("BAILIAN_API_KEY"),
    streaming= True,
)