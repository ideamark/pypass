# Overview
* pyDDNS is a simple python server for DDNS serve

# How to use
* First, you should have an independent IP server, like Aliyun ECS or other VPS.
* Second, scp the proxy folder to the independent IP server.
* Third, enter the independent IP server's IP into proxy.py and heart_beat.py.
* Finally, run proxy.py on your independent IP server and run heart_beat.py in your local server.

# How it works
* The local server send the public IP to the remote server by sending heart beat signal (UDP).
* The remote server will get the local public IP and transfer the ports by using socket.
* The code also check the port which it opend, if close, it can reconnect automatically.

# About the author
* Name: Mark Young
* Email: ideamark@qq.com
