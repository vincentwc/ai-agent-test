import asyncio
import time

from langchain_core.prompts import PromptTemplate
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage, ToolMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver

from app.code_agent.agent.fie_server import FileServer
from app.code_agent.model.qwen import llm_qwen
from app.code_agent.rag.rag import retrieve_index, create_client, query_rag_from_bailian
from app.code_agent.tools.file_tools import file_tools
from app.code_agent.tools.shell_tools import get_stdio_shell_tools
from app.code_agent.tools.terminal_tools import get_stdio_terminal_tools


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
    terminal_tools = await get_stdio_terminal_tools()
    tools = file_tools + terminal_tools

    # 方案二：提供一个rag工具，让智能体通过工具查询知识

    prompt = PromptTemplate.from_template(template="""
    # 角色
    你是一名优秀的工程师，你的名字叫做{name}

    # 重要：终端工具使用规范（必须严格遵守）
    终端工具有4个：close_terminal、open_terminal、run_terminal_script、get_terminal_text
    它们有严格的执行顺序和依赖关系：

    1. close_terminal：关闭所有现有终端
    2. open_terminal：打开新终端
    3. run_terminal_script：在终端中执行脚本命令
    4. get_terminal_text：获取终端输出文本

    **关键规则**：
    - 每一次只能调用1个工具
    - 必须等待当前工具执行完成并查看结果后，才能调用下一个工具
    - 绝对不能同时调用多个工具
    - 根据每个工具的返回结果判断是否需要继续调用下一个工具
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

        # res = None
        # async for event in agent.astream(input={"messages": user_input}, config=config):
        #     print("event:", event)
        #     if "messages" in event:
        #         res = event
        #
        # if res:
        #     print("助理: ", res["messages"][-1].content)
        # print()

        iteration_count = 0
        start_time = time.time()
        last_tool_time = start_time

        # 方案一： 从阿里云百炼知识库中读取知识，并拼接到提示词中
        rag = query_rag_from_bailian(user_input)

        prompt = f"""
        # 相关知识
        {rag}

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
