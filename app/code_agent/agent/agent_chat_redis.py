from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.redis import RedisSaver
from langchain.agents import create_agent

from app.code_agent.model.qwen import llm_qwen
from app.code_agent.tools.file_tools import file_tools


def create_my_agent():
    # memory = MemorySaver()

    # redis 作为 checkpointer
    with RedisSaver.from_conn_string("redis://localhost:63380/0") as memory:

        memory.setup()

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
            input={"messages": [("user", "我们刚才聊了什么")]},
            config=config,
            debug=True,
    ):
        print(chunk, end="")

    print("=" * 50)

    # for chunk in agent.stream(
    #         input={"messages": [("user", "我是谁")]},
    #         config=config,
    #         debug=True,
    # ):
    #     print(chunk, end="")


if __name__ == "__main__":
    run_agent()
