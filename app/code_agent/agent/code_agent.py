import asyncio

from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig

from app.code_agent.agent.fie_server import FileServer
from app.code_agent.model.qwen import llm_qwen
from app.code_agent.tools.file_tools import file_tools
from app.code_agent.tools.shell_tools import get_stdio_shell_tools


async def run_agent():
    memory = FileServer()

    shell_tools = await get_stdio_shell_tools()

    tools = file_tools + shell_tools

    agent = create_agent(
        model=llm_qwen,
        tools=tools,
        checkpointer=memory,
        debug=False
    )

    config = RunnableConfig(configurable={"thread_id": 12})

    while True:
        user_input = input("用户:  ")

        if user_input.lower() in ["exit", "quit"]:
            break

        res = None
        async for event in agent.astream(input={"messages": user_input}, config=config):
            print("event:", event)
            if "messages" in event:
                res = event

        if res:
            print("助理: ", res["messages"][-1].content)
        print()



asyncio.run(run_agent())