import subprocess



def run_applescript(script: str):
    p = subprocess.Popen(["osascript", "-e", script],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    output, error = p.communicate()
    return output.decode("utf-8").strip(), error.decode("utf-8").strip()


def close_terminal_if_open():
    """关闭 Terminal 应用（如果正在运行）"""
    output, error = run_applescript("""
tell application "System Events"
    if exists (application processes whose name is "Terminal") then
        tell application "Terminal" to quit
    end if
end tell
""")
    if error:
        return False
    else:
        return True


def open_new_terminal(window_id: str = "") -> bool | tuple[str, str]:
    """打开新的 Terminal 窗口"""
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
        output, error = run_applescript(f"""
tell application "Terminal"
    if (count of windows) > 0 then
        activate
    else
        activate 
    end if
end tell
""")
    if error:
        return False
    else:

        return get_all_terminal_window_ids()

def get_all_terminal_window_ids():
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
    return output, error


def run_script_in_terminal(script: str):
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
        return False
    else:
        return output

def get_terminal_full_text():
    output, error = run_applescript(f"""
tell application "Terminal"
    set fullText to history of selected tab of front window
end tell
""")
    if error:
        return False
    else:
        return output



if __name__ == '__main__':
    # close_terminal_if_open()
    # window_ids = open_new_terminal()
    # print(window_ids)
    run_script_in_terminal("pwd")
    full_text = get_terminal_full_text()
    print(full_text)
