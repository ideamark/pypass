# Overview
* pyDDNS is a simple python DDNS server which is just like Oray server.
* But it is faster and more stable than Oray server.

# How to use
* First, you should have an independent IP server as your remote server, like Aliyun ECS or other VPS.
* Second, scp the proxy folder to your remote server.
* Third, enter the remote server's IP into proxy.py and heart_beat.py.
* Finally, run proxy.py on your remote server and run heart_beat.py on your local server.

# How it works
* The local server send the public IP to the remote server by sending heart beat signal (UDP).
* The remote server will get the local public IP and transfer the ports between remote and local by socket.
* The code can also check the port which it opend is open or close, if close, it can reconnect automatically.

# About the author
* Name: Mark Young
* Email: ideamark@qq.com
