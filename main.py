from langchain_ollama.chat_models import  ChatOllama


if __name__ == "__main__":
    llm = ChatOllama(model= "qwen3:4b")
    resp = llm.invoke("你好,你是谁?")
    print(resp.content)
