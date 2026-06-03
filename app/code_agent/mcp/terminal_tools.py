import subprocess
import time
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
    set resultText to ""
    repeat with aWindow in windows
        set wid to id of aWindow
        set tabCount to number of tabs of aWindow
        repeat with i from 1 to tabCount
            set resultText to resultText & "窗口ID: " & wid & " 标签页: " & i & linefeed
        end repeat
    end repeat
    return resultText
end tell
""")
    if error:
        return error
    return output


@mcp.tool(name="close_terminal", description="关闭终端应用程序")
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
        return f"关闭 Terminal 失败: {error}"
    else:
        return "Terminal 已成功关闭"


@mcp.tool(name="open_terminal", description="打开新的终端窗口")
def open_new_terminal(
        window_id: Annotated[str, Field(description="可选的窗口ID，为空则打开新窗口", examples="12345")] = "",
) -> str:
    """打开新的终端窗口或激活指定的窗口"""
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
end tell""")
    else:
        output, error = run_applescript("""
tell application "Terminal"
    if (count of windows) > 0 then
        activate
    else
        activate
    end if
end tell""")
    if error:
        return f"打开 Terminal 失败: {error}"
    else:
        time.sleep(2)  # 等待 Terminal 打开
        window_ids = get_all_terminal_window_ids()
        return f"Terminal 已成功打开，窗口ID: {window_ids}"


@mcp.tool(name="run_terminal_script", description="在终端中运行脚本命令并返回执行结果")
def run_terminal_script(
        script: Annotated[str, Field(description="要在终端中运行的脚本命令", examples="ls -al")],
) -> str:
    """在终端中运行脚本命令并等待执行结果"""
    safe_script = script.replace('"', '\\"')
    output, error = run_applescript(f"""
tell application "Terminal"
    activate
    if (count of windows) > 0 then
        do script "{safe_script}" in window 1
    else
        do script "{safe_script}"
    end if
end tell
""")
    if error:
        return error
    return output or "脚本已成功执行"



@mcp.tool(name="get_terminal_text", description="获取终端的完整文本内容")
def get_terminal_full_text() -> str:
    """获取终端的完整文本内容"""
    output, error = run_applescript("""
tell application "Terminal"
    set fullText to history of selected tab of front window
end tell""")
    if error:
        return f"获取终端文本失败: {error}"
    return output


if __name__ == '__main__':
    mcp.run(transport="stdio")
