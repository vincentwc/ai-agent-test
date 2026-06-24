import asyncio
import time

from langchain_core.prompts import PromptTemplate
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage, ToolMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from app.code_agent.agent.fie_server import FileServer
from app.code_agent.model.qwen import llm_qwen
from app.code_agent.rag.rag import query_rag_from_bailian
from app.code_agent.tools.browser_tools import get_stdio_browser_tools
from app.code_agent.tools.file_tools import file_tools
from app.code_agent.tools.mysql_tools import get_stdio_mysql_tools
from app.code_agent.tools.rag_tools import get_stdio_rag_tools
from app.code_agent.tools.terminal_tools import get_stdio_terminal_tools
from app.code_agent.tools.vm import get_stdio_vm_tools


def format_debug_output(step_name: str, content: str, is_tool_call: bool = False) -> None:
    if is_tool_call:
        print(f"♻️【工具调用】{step_name}")
        print("-" * 40)
        print(content)
        print("-" * 40)
    else:
        print(f"💭 【{step_name}】")
        print("-" * 40)
        print(content)
        print("-" * 40)


async def run_agent():
    memory = FileServer()
    # memory = MemorySaver()

    # shell_tools = await get_stdio_shell_tools()
    # terminal_tools = await get_stdio_terminal_tools()
    # rag_tools = await get_stdio_rag_tools()
    # vm_tools = await get_stdio_vm_tools()
    mysql_tools = await get_stdio_mysql_tools()

    # browser_tools = await get_stdio_browser_tools()
    tools = mysql_tools

    # 方案二：提供一个rag工具，让智能体通过工具查询知识

    prompt = PromptTemplate.from_template(template="""
# 角色
你是一名优秀的工程师，你的名字叫做{name}

# 要求
执行任务之前先使用 query_rag 工具查询知识库，根据知识库中的知识执行任务
""")

    agent = create_react_agent(
        model=llm_qwen,
        tools=tools,
        checkpointer=memory,
        debug=False,
        prompt=SystemMessage(content=prompt.format(name="Bot")),
    )

    config = RunnableConfig(configurable={"thread_id": 10})

    while True:
        user_input = input("用户:  ")

        if user_input.lower() in ["exit", "quit"]:
            break

        print("\n🤖 助手正在思考和处理...")
        print("=" * 50)

        iteration_count = 0
        start_time = time.time()
        last_tool_time = start_time

        # 方案一： 从阿里云百炼知识库中读取知识，并拼接到提示词中
        # rag = query_rag_from_bailian(user_input)

        prompt = f"""
        # 相关知识

        # 用户问题
        {user_input}
        """

        async for chunk in agent.astream(input={"messages": prompt}, config=config):
            iteration_count += 1

            print(f"\n📉 第{iteration_count}步执行:")
            print("-" * 30)

            items = chunk.items()

            for node_name, node_output in items:
                # print(f"{node_name}: {node_output}")
                if "messages" in node_output:
                    for msg in node_output["messages"]:
                        if isinstance(msg, AIMessage):
                            if msg.content:
                                format_debug_output("AI思考", str(msg.content))
                            else:
                                for tool in msg.tool_calls:
                                    format_debug_output("工具调用", f"{tool['name']}:{tool['args']}")
                        elif isinstance(msg, ToolMessage):
                            tool_name = getattr(msg, "name", "unknown")
                            tool_content = msg.content

                            current_time = time.time()
                            tool_duration = current_time - last_tool_time
                            last_tool_time = current_time

                            tool_result = f"""🔧 工具:{tool_name}
📩结果:
{tool_content}
✅状态：执行完成，可以开始下一个任务
⏰执行时间: {tool_duration:.2f}秒"""

                            format_debug_output("工具执行结果", tool_result, is_tool_call=True)
                        else:
                            format_debug_output("未实现", f"暂未实现的打印内容{chunk}")

        print()


asyncio.run(run_agent())
