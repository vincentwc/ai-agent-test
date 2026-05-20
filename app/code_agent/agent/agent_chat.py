from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents import create_agent

from app.code_agent.model.qwen import llm_qwen
from app.code_agent.tools.file_tools import file_tools


def create_my_agent():
    memory = MemorySaver()

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
            input={"messages": [("user", "你好,我是vincent")]},
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
