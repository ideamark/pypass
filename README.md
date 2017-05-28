# pyDDNS V1.0.1

## Overview
* pyDDNS is a simple python DDNS server which is just like Oray server.
* But it is faster and more stable than Oray server.

## How to use
* First, you should have an independent IP server as your remote server, like Aliyun ECS or other VPS. And scp the proxy folder to your remote server.
* Then, enter the configure value in the heart_beat.py and proxy.py. 
* Finally, run heart_beat.py on your local server and run proxy.py on your remote server, wait for the heart beat send to proxy.py, if it displays "Got a heart beat" and "home ip is written", it means connection is succeeded. 

## how to execute when boot up
* Add this to /etc/rc.local before "exit 0":
 * your_dir/heart_beat.py &

## How does it work
* The local server send the public IP to the remote server by sending heart beat signal (UDP).
* The remote server will get the local public IP and transfer the ports between remote and local by socket.
* The code can also check the port which it opend is open or close, if close, it can reconnect automatically.

## To know more
* Author: Mark Young
* Email: ideamark@qq.com
