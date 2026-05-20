import uuid

from langchain_core.runnables import RunnableWithMessageHistory, RunnableConfig

from app.code_agent.prompts.multi_chat_prompt import multi_chat_prompt
from app.code_agent.model.qwen import llm_qwen
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_community.agent_toolkits.file_management import FileManagementToolkit
from langchain_core.runnables import RunnableSequence


# from langchain.agents import create_agent

def get_session_history(session_id: str):
    return FileChatMessageHistory(f"{session_id}.json")


file_toolkit = FileManagementToolkit(root_dir="/Users/vincent/developEnv/llm/.temp")
file_tools = file_toolkit.get_tools()

# agent = create_agent(model=llm_qwen, tools=file_tools)

llm_with_tools = llm_qwen.bind_tools(tools=file_tools)


# 串行写法1
# chain = multi_chat_prompt.pipe(llm_with_tools).pipe(StrOutputParser())

# 串行写法2
chain = multi_chat_prompt | llm_with_tools | StrOutputParser()
# chain = multi_chat_prompt | agent

# 串行写法3
chain = RunnableSequence(first=multi_chat_prompt, middle=[llm_with_tools], last=StrOutputParser())


chain_with_history = RunnableWithMessageHistory(
    runnable=chain,
    get_session_history=get_session_history,
    input_messages_key="question",
    history_messages_key="chat_history",
)

chat_session_id = uuid.uuid4()

while True:
    user_input = input("用户:  ")
    if user_input.lower() in ["exit", "quit"]:
        break

    print("助理: ", end="")
    for chunk in chain_with_history.stream(
            {"question": user_input},
            config=RunnableConfig(configurable={"session_id": chat_session_id}),
    ):
        print(chunk, end="")

    print("\n")
