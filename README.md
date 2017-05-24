# pyDDNS V1.0.1

## Overview
* pyDDNS is a simple python DDNS server which is just like Oray server.
* But it is faster and more stable than Oray server.

## How to use
* First, you should have an independent IP server as your remote server, like Aliyun ECS or other VPS. And scp the proxy folder to your remote server.
* Second, Enter your local server's public IP into proxy/home_ip.txt. You can search the key word "IP" by Baidu to get the public IP. PS: This step only do once, after that the proxy.py could write the public IP into home_ip.txt automatically. 
* Third, enter the remote server's IP into proxy.py and heart_beat.py.
* Finally, run proxy.py on your remote server and run heart_beat.py on your local server.

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
