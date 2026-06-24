from app.code_agent.uitls.mcp import create_mcp_stdio_client

async def get_stdio_mysql_tools():
    params = {
        "command": "python",
        "args": [
            "/Users/vincent/developEnv/code/ai/ai-agent-test/app/code_agent/mcp/mysql_tools.py"
        ],
    }

    client,tools = await create_mcp_stdio_client("mysql_tools", params)

    return tools
