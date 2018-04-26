# pyPass

## Overview
* pyPass is a simple and powerful remote ports mapping tool.

## How to use
1. Make sure you have installed python3, python3-pip. If not, install them before next step.
2. Run command "git clone https://github.com/ideamark/pyPass" to download pyPass to your local server.
3. Write params to "config" file.
4. Copy the whole pyPass folder to the remote server.
5. Run local.py on local server and run remote.py on remote server. And then it works. U can access your local server ports by access your remote server ports.
6. If there is an error like: "No module named 'xxx'", run command: "sudo pip3 install xxx" to install the lost module.

## Execute when boot up
* For Ubuntu, write this command in /etc/rc.local before "exit 0":
 * "nohup python3 pyPass/local.py &"

## Seek more
* Author: Mark Young
* Email: ideamark@qq.com
* The basic code comes from https://github.com/aploium/shootback, the author is Aploium, thanks for the sharing.
