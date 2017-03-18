#!/usr/bin/env python3
import sys, os
import socket, select
import time

class Proxy:
    def __init__(self, proxy_addr, home_addr):
        self.home_addr = home_addr
        self.proxy_addr = proxy_addr
        self.proxy = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.proxy.bind(self.home_addr)
        self.proxy.listen(10)
        self.inputs = [self.proxy]
        self.route = {}

    def serve_forever(self):
        print(self.proxy_addr,self.home_addr,'listen...')
        while True:
            readable, _, _ = select.select(self.inputs, [], [])
            for self.sock in readable:
                if self.sock == self.proxy:
                    self.on_join()
                else:
                    data = self.sock.recv(8096)
                    if not data:
                        self.__del__()
                    else:
                        self.route[self.sock].send(data)

    def on_join(self):
        client, addr = self.proxy.accept()
        print(addr,'connect')
        forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        forward.connect(self.proxy_addr)
        self.inputs += [client, forward]
        self.route[client] = forward
        self.route[forward] = client

    def __del__(self):
        for s in self.sock, self.route[self.sock]:
            self.inputs.remove(s)
            del self.route[s]
            s.shutdown(2)
            s.close()

def proxy_server(proxy_ip, home_port, proxy_port):
    f = open('home_ip.txt','r')
    home_ip = f.read().replace('\n','')
    f.close()
    try:
        Proxy((home_ip,home_port),(proxy_ip,proxy_port)).serve_forever()
    except KeyboardInterrupt:
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
    HOST = ''    # Your remote server IP
    PORT = 2010    # Your remote server port for heart beat

    import threading
    ts = []
    ports = [(22,2222),(2080,80)]    # Add your ports here
    for p1, p2 in ports:
        ts.append(threading.Thread(target=proxy_server,args=(HOST,p1,p2,)))
    for t in ts:
        t.setDaemon(True)
        t.start()
    time.sleep(1)

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
                home_ip = str(address[0])
                f = open('home_ip.txt','w')
                f.write(home_ip)
                f.close()
                print('home ip is written')
                message = bytes('#OK',encoding = 'utf-8')
                s.sendto(message, address)
                print('Return OK')

            # Check if port is opened, if not, reconnect
            for p1, p2 in ports:
                if not is_open(HOST, p2):
                    t = threading.Thread(target=proxy_server,args=(HOST,p1,p2,))
                    t.setDaemon(True)
                    t.start()
                    print('port %d is reconnected' % p2)

        except (KeyboardInterrupt, SystemExit):
            raise
