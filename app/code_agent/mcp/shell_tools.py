import subprocess
import shlex


def run_shell_command(command):
    """
    运行shell命令
    """
    try:
        shell_command = shlex.split(command)

        if  shell_command[0] == 'rm':
            return Exception('不允许使用rm')

        res = subprocess.run(shell_command, shell=True, capture_output=True, text=True)


        if res.returncode != 0:
            return res.stderr
        return res.stdout
    except Exception as e:
        return str(e)


if __name__ == '__main__':
    ret = run_shell_command('ls -al | grep terminal')
    print(ret)
