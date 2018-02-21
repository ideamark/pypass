# pyPass

## Overview
* pyPass is an easy config TCP tunnel server to map local ports to remote ports.
* The basic code comes from https://github.com/aploium/shootback, the author is Aploium, thanks for the sharing.

## How to use
1. make sure you have installed python3, python3-pip. If not, install them before next step.
2. "git clone https://github.com/ideamark/pyPass" to download pyPass to your local server.
3. Write params to "config" file.
4. Copy the whole pyPass folder to the remote server.
5. Execute local.py on local server and execute remote.py on remote server. Then access the remote ports will access your local ports!

## how to execute when boot up
* Written command in /etc/rc.local before "exit 0"

## Seek more
* Author: Mark Young
* Email: ideamark@qq.com
