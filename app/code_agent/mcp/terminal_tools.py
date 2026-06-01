import subprocess
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP()


def run_applescript(script: str):
    p = subprocess.Popen(["osascript", "-e", script],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    output, error = p.communicate()
    return output.decode("utf-8").strip(), error.decode("utf-8").strip()

def get_all_terminal_window_ids() -> str:
    """获取所有 Terminal 窗口的 ID"""
    output, error = run_applescript("""
tell application "Terminal"
    set outputList to {}
    repeat with aWindow in windows
        set windowID to id of aWindow
        set tabCount to number of tabs of aWindow
        repeat with tabIndex from 1 to tabCount
            set end of outputList to {tab tabIndex of window id windowID}
        end repeat
    end repeat
end tell
return outputList
""")
    if error:
        return error
    return output

@mcp.tool(name="close_terminal", description="如果 Terminal 正在运行则关闭")
def close_terminal_if_open() -> str:
    """关闭 Terminal 应用（如果正在运行）"""
    output, error = run_applescript("""
tell application "System Events"
    if exists (application processes whose name is "Terminal") then
        tell application "Terminal" to quit
    end if
end tell
""")
    if error:
        return error
    return output or "Terminal 已成功关闭"


@mcp.tool(name="open_terminal", description="打开或激活 Terminal 窗口")
def open_new_terminal(
        window_id: Annotated[str, Field(description="要激活的 Terminal 窗口 ID", examples=["12345"])] = "",
) -> str:
    """打开或激活 Terminal 窗口"""
    if window_id:
        output, error = run_applescript(f"""
tell application "Terminal"
    if (count of windows) > 0 then
        set activeWindow to window id {window_id}
        set frontmost of activeWindow to true
        activate
    else
        activate 
    end if
end tell
""")
    else:
        output, error = run_applescript("""
tell application "Terminal"
    if (count of windows) > 0 then
        activate
    else
        activate 
    end if
end tell
""")
    if error:
        return error
    window_output, window_error = get_all_terminal_window_ids()
    if window_error:
        return window_error
    return window_output or output


@mcp.tool(name="run_terminal_script", description="在 Terminal 中运行 shell 脚本")
def run_terminal_script(
        script: Annotated[str, Field(description="要在 Terminal 中执行的 shell 脚本", examples=["ls -al"])],
) -> str:
    """在 Terminal 中执行脚本"""
    output, error = run_applescript(f"""
tell application "Terminal"
    activate
    if (count of windows) > 0 then
        do script "{script}" in window 1
    else
        do script "{script}"
    end if
end tell
""")
    if error:
        return error
    return output or "脚本已成功执行"


@mcp.tool(name="get_terminal_text", description="获取当前 Terminal 标签页的完整文本历史")
def get_terminal_full_text() -> str:
    """获取当前 Terminal 标签页的完整文本"""
    output, error = run_applescript("""
tell application "Terminal"
    set fullText to history of selected tab of front window
end tell
""")
    if error:
        return error
    return output


if __name__ == '__main__':
    mcp.run(transport="stdio")
