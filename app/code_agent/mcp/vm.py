import os
import shlex
import subprocess
import tempfile
from typing import Annotated

from mcp.server.fastmcp import FastMCP

mcp = FastMCP()


def run_limavm_shell_command(command):
    """
    运行shell命令
    """
    try:
        wrapper_command = "limactl shell lima-test " + command
        shell_command = shlex.split(wrapper_command)
        res = subprocess.run(shell_command, shell=False, capture_output=True, text=True)

        if res.returncode != 0:
            return res.stderr
        return res.stdout
    except Exception as e:
        return str(e)


def run_limavm_command(command):
    """
    运行shell命令
    """
    try:
        wrapper_command = "limactl " + command
        shell_command = shlex.split(wrapper_command)
        res = subprocess.run(shell_command, shell=False, capture_output=True, text=True)

        if res.returncode != 0:
            return res.stderr
        return res.stdout
    except Exception as e:
        return str(e)


from pydantic import Field


@mcp.tool(name="make_dir_in_vm", description="在指定的虚拟机中创建目录，相当于mkdir -p命令")
def make_dir_in_vm(dir_path: Annotated[
    str, Field(description="要创建的目录路径", examples="/home/vincent.guest/nginx/uploads/test3")]):
    """
    在虚拟机中创建目录
    :param dir_path: 目录路径
    :return:
    """
    print("dir_path", dir_path)
    return run_limavm_shell_command(f"mkdir -p {dir_path}")


@mcp.tool(name="list_files_in_vm", description="查看指定的虚拟机中指定目录下的文件，相当于ls -al命令")
def list_files_in_vm(dir_path: Annotated[
    str, Field(description="要查看的目录路径", examples="/home/vincent.guest/nginx/uploads/")]):
    """
    查看虚拟机指定目录下的文件
    :param dir_path: 目录路径
    :return:
    """
    return run_limavm_shell_command(f"ls -al {dir_path}")


@mcp.tool(name="write_file_to_vm", description="在指定的虚拟机中写入文件")
def write_file_to_vm(
        file_path: Annotated[
            str, Field(description="要写入的文件路径", examples="/home/vincent.guest/nginx/uploads/tests/index.html")],
        content: Annotated[str, Field(description="要写入的文件内容", examples="<div>hello world</div>")]):
    with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as tmp_file:
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    print("本地临时文件已创建", tmp_file_path)
    run_limavm_command(f"""copy {tmp_file_path} lima-test:{file_path}""")
    change_file_permission_in_vm(file_path, "755")


def change_file_permission_in_vm(file_path, mode):
    return run_limavm_shell_command(f"chmod {mode} {file_path}")


@mcp.tool(name="upload_directory_to_vm", description="将本地文件目录上传至虚拟机指定目录")
def upload_directory_to_vm(
        local_dir: Annotated[str, Field(description="本地文件目录",examples="/Users/vincent/developEnv/llm/.temp/project/vue2-project")],
        vm_dest_dir: Annotated[str, Field(description="虚拟机文件目录", examples="/home/vincent.guest/nginx/uploads/vue2-project")]):
    if not os.path.exists(local_dir):
        msg = f"本地目录不存在: {local_dir}"
        print(f"[upload] {msg}")
        return msg

    if not os.path.isdir(local_dir):
        msg = f"指定路径不是文件夹: {local_dir}"
        print(f"[upload] {msg}")
        return msg

    make_dir_in_vm(vm_dest_dir)

    for root, dirs, files in os.walk(local_dir):
        if 'node_modules' in dirs:
            dirs.remove('node_modules')
        if '.git' in dirs:
            dirs.remove('.git')

        rel_path = os.path.relpath(root, local_dir)
        #         创建远程文件夹
        vm_subdir = os.path.join(vm_dest_dir, rel_path)
        make_dir_in_vm(vm_subdir)
        #         上传文件
        for file_name in files:
            real_file_path = os.path.join(root, file_name)
            vm_file_path = os.path.join(vm_subdir, file_name)
            result = run_limavm_command(f"""copy {real_file_path} lima-test:{vm_file_path}""")

    return f"上传 [{local_dir}] 目录至 lima-test:{vm_dest_dir} 成功"


if __name__ == '__main__':
    # mcp.run(transport="stdio")
    # result = run_limavm_shell_command("ls -al /home/vincent.guest/nginx/uploads")
    # print(result)
    # r = make_dir_in_vm("/home/vincent.guest/nginx/uploads/test3")
    # print(r)

    # r = list_files_in_vm("/home/vincent.guest/nginx/uploads")
    # print(r)

    # print(write_file_to_vm("/home/vincent.guest/nginx/uploads/tests/index.html", "<div>hello world</div>"))

    result = upload_directory_to_vm(local_dir="/Users/vincent/developEnv/llm/.temp/project/vue2-project",
                                    vm_dest_dir="/home/vincent.guest/nginx/uploads/vue2-project")
    print(result)
