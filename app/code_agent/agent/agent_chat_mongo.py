from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.mongodb import MongoDBSaver
from langchain.agents import create_agent
from pymongo import MongoClient

from app.code_agent.model.qwen import llm_qwen
from app.code_agent.tools.file_tools import file_tools


def create_my_agent():

    client = MongoClient("mongodb://root:yy920812@localhost:27017")
    memory = MongoDBSaver(client, db_name="chat")

    agent = create_agent(
        model=llm_qwen,
        tools=file_tools,
        checkpointer=memory,
        debug=True,
    )

    return agent


config = RunnableConfig(configurable={"thread_id": 1})


def run_agent():
    agent = create_my_agent()

    for chunk in agent.stream(
            input={"messages": [("user", "你好，我是vincent")]},
            config=config,
            debug=True,
    ):
        print(chunk, end="")

    print("=" * 50)

    for chunk in agent.stream(
            input={"messages": [("user", "我是谁")]},
            config=config,
            debug=True,
    ):
        print(chunk, end="")


if __name__ == "__main__":
    run_agent()
