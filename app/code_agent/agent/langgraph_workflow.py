from langchain_core.messages import AIMessage
from langchain_core.prompt_values import StringPromptValue
from langgraph.constants import START, END
from langgraph.graph import MessagesState, StateGraph

from app.code_agent.mcp.browser_tools import search_in_baidu_with_html
from app.code_agent.model.qwen import llm_qwen

key_extract_query_keyword = "key_extract_query_keyword"
key_search_baidu = "key_search_baidu"
key_reply_user = "key_reply_user"


def node_extract_query_keyword(state: MessagesState):
    last_message = state["messages"][-1]
    content = last_message.content
    prompt = StringPromptValue(text=f"请从如下信息中提取需要在百度中搜索的关键词，直接返回最终结果：{content}")
    message = llm_qwen.invoke(input=prompt)
    state["messages"].append(message)
    return state


def node_search_baidu(state: MessagesState):
    last_message = state["messages"][-1]
    keyword = last_message.content
    html = search_in_baidu_with_html(keyword)
    state["messages"].append(AIMessage(content=f"百度搜索结果：{html}"))
    return state


def node_extract_reply_user(state: MessagesState):
    question = state["messages"][0].content
    baidu_search_content = state["messages"][-1].content
    result = llm_qwen.invoke(input=f"""
# 要求
请结合百度搜索的结果，回答用户的问题:{question}

# 百度搜索结果
{baidu_search_content}
""")
    state["messages"].append(result)
    return state


state_graph = StateGraph(MessagesState)
state_graph.add_node(key_extract_query_keyword, node_extract_query_keyword)
state_graph.add_node(key_search_baidu, node_search_baidu)
state_graph.add_node(key_reply_user, node_extract_reply_user)

state_graph.add_edge(START, key_extract_query_keyword)
state_graph.add_edge(key_extract_query_keyword, key_search_baidu)
state_graph.add_edge(key_search_baidu, key_reply_user)
state_graph.add_edge(key_reply_user, END)

compile_graph = state_graph.compile()

results = compile_graph.stream({
    "messages": [{"role": "user", "content": "请问北京今天天气如何？"}]
})

for s in results:
    print(s)
    key = list(s)[0]
    print(s[key]["messages"][-1].content)
    print("-" * 60)
