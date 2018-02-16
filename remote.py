#!/usr/bin/env python3
import os
import select
import socket
import sys
import time


# First Configure
try:
    HOST = ''    # Your remote server IP, the type is string
    PORT =     # Your remote server port for heart beat, the type is int
    PROXY_LIST = [(,), (,)]    # Add your (local prot, remote port) here
except:
    print('Configure Value Error')


class Remote(object):

    def __init__(self, local_addr, remote_addr):
        self.local_addr = local_addr
        self.remote_addr = remote_addr
        self.remote = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.remote.bind(self.remote_addr)
        self.remote.listen(10)
        self.inputs = [self.remote]
        self.route = {}

    def serve_forever(self):
        print(self.local_addr,self.remote_addr,'listen...')
        while True:
            readable, _, _ = select.select(self.inputs, [], [])
            for self.sock in readable:
                if self.sock == self.remote:
                    self.on_join()
                else:
                    data = self.sock.recv(8096)
                    if not data:
                        self.__del__()
                    else:
                        self.route[self.sock].send(data)

    def on_join(self):
        client, addr = self.remote.accept()
        print(addr,'connect')
        forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        forward.connect(self.local_addr)
        self.inputs += [client, forward]
        self.route[client] = forward
        self.route[forward] = client

    def __del__(self):
        for s in self.sock, self.route[self.sock]:
            self.inputs.remove(s)
            del self.route[s]
            s.shutdown(2)
            s.close()


def remote_server(local_port, remote_port):
    f = open('local_ip.txt','r')
    local_ip = f.read().replace('\n','')
    f.close()
    try:
        Remote((local_ip,local_port),(HOST,remote_port)).serve_forever()
    except (KeyboardInterrupt):
        sys.exit(1)


def is_open(ip, port):
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    try:
        s.connect((ip,int(port)))
        s.shutdown(2)
        print('%d is open' % port)
        return True
    except:
        print('%d is down' % port)
        return False


if __name__ == '__main__':
    import threading
    ts = []
    for p1, p2 in PROXY_LIST:
        ts.append(threading.Thread(target=remote_server,args=(p1,p2,)))
    for t in ts:
        t.setDaemon(True)
        t.start()
    time.sleep(5)

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    print('Start reciving heart beat ...')

    while True:
        try:
            # Check heart beat
            message, address = s.recvfrom(5)
            if message == b'#Hi':
                print('Got a heart beat')
                local_ip = str(address[0])
                f = open('local_ip.txt','w')
                f.write(local_ip)
                f.close()
                print('home ip is written')

            # Check if port is opened, if not, reconnect
            for p1, p2 in PROXY_LIST:
                if not is_open(HOST, p2):
                    t = threading.Thread(target=remote_server,args=(p1,p2,))
                    t.setDaemon(True)
                    t.start()
                    print('port %d is reconnected' % p2)

        except (KeyboardInterrupt, SystemExit):
            sys.exit(1)
