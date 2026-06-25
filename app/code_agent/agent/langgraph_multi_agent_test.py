from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent
from langchain.agents import create_agent
from app.code_agent.model.qwen import llm_qwen


def add(a: float, b: float) -> float:
    """add two numbers"""
    return a + b


def multiply(a: float, b: float) -> float:
    """multiply two numbers"""
    return a * b


def web_search(question: str) -> str:
    """search the web for information"""
    return (
        "Here are the headcounts for each of the FAANG companies in 2024:\n"
        "1. **Facebook (Meta)**: 67,317 employees.\n"
        "2. **Apple**: 164,000 employees.\n"
        "3. **Amazon**: 1,551,000 employees.\n"
        "4. **Netflix**: 14,000 employees.\n"
        "5. **Google (Alphabet)**: 181,269 employees."
    )


math_agent = create_agent(
    model=llm_qwen,
    tools=[add, multiply],
    name="math_expert",
    system_prompt="你是一个数学专家，一次执行只使用一个工具"
)

research_agent = create_agent(
    model=llm_qwen,
    tools=[web_search],
    name="research_expert",
    system_prompt="你是一个世界级调研专家，能够使用web_search工具，不要使用任何数学工具。"
)

workflow = create_supervisor(
    agents=[math_agent, research_agent],
    model=llm_qwen,
    prompt=(
        "You are a team supervisor managing a research expert and a math expert. "
        "For current events, use research_agent. "
        "For math problems, use math_agent."
    )
)

app = workflow.compile()

for chunk in app.stream({
    "messages": [
        {
            "role": "user",
            "content": "what's the combined headcount of the FAANG companies in 2024?"
        }
    ]
}):
    print(chunk)
