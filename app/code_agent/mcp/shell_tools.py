import subprocess
from typing import Annotated
from pydantic import Field
from mcp.server.fastmcp import FastMCP

mcp = FastMCP()


@mcp.tool(name="run_shell", description="Run a shell command")
def run_shell_command(
        command: Annotated[str, Field(description="shell command will be executed", examples=["ls -al"])]) -> str:
    """
    运行shell命令
    """
    try:
        if command.startswith('rm'):
            return '不允许使用rm'

        res = subprocess.run(command, shell=True, capture_output=True, text=True)

        if res.returncode != 0:
            return res.stderr
        return res.stdout
    except Exception as e:
        return str(e)


def run_shell_command_by_popen(commends):
    p = subprocess.Popen(commends, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = p.communicate()
    if stdout:
        return stdout
    return stderr


if __name__ == '__main__':
    # ret = run_shell_command('rm -rf')
    # print(ret)

    # ret = run_shell_command_by_popen('ls -al | grep shell')
    # print(ret)
    mcp.run(transport="stdio")
