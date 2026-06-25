import asyncio

from langchain.agents import create_agent
from langchain_core.messages import convert_to_messages
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph_supervisor import create_supervisor

from app.code_agent.model.qwen import llm_qwen
from app.code_agent.tools.file_tools import file_tools
from app.code_agent.tools.shell_tools import get_stdio_shell_tools


def pretty_print_message(update, last_message=False):
    for node_name, node_update in update.items():
        update_label = f"update from node {node_name}"
        print(update_label)
        print("\n")
        messages = convert_to_messages(node_update["messages"])
        if last_message:
            messages = messages[-1:]

        for message in messages:
            pretty_message = message.pretty_repr(html=True)
            print(pretty_message)

        print("\n\n")

async def run_agent():
    memory = MemorySaver()

    shell_tools = await get_stdio_shell_tools()

    research_agent = create_agent(
        model=llm_qwen,
        tools=shell_tools + file_tools,
        name="research_expert",
        system_prompt="你是一个技术方案专家，专门负责设计技术方案，请不要直接写代码"
    )

    code_agent = create_agent(
        model=llm_qwen,
        tools=shell_tools,
        name="code_expert",
        system_prompt="你是一个编程专家，请根据 research_expert 设计的技术方案，编写代码"
    )

    supervisor_agent = create_supervisor(
        agents=[research_agent, code_agent],
        model=llm_qwen,
        prompt=(
            "You are a team supervisor managing a research expert and a code expert."
            "For task planning and task researching, use research_agent."
            "For code problems, use code_agent."
        )
    )

    app = supervisor_agent.compile(checkpointer=memory)

    while True:
        user_input = input("用户: ")

        if user_input.lower() == "exit":
            break

        config = RunnableConfig(
            configurable={
                "thread_id": 1
            }
        )
        async for chunk in app.astream(input={"messages": user_input}, config=config):
            pretty_print_message(chunk,last_message=True)

asyncio.run(run_agent())