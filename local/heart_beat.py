#!/usr/bin/env python3
import socket, sys, time

def base():
    HOST = '123.57.230.28'
    PORT = 2010
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        port = int(PORT)
    except ValueError:
        port = socket.getservbyname(PORT, 'udp')
    s.connect((HOST, port))
    s.settimeout(5)
    while True:
        try:
            s.sendall(b'#Hi')
            print('Send a heart beat')
            buf = s.recv(5)
            if not len(buf):
                break
            elif buf == b'#OK':
                print('Recive OK')
            time.sleep(2)
        except KeyboardInterrupt:
            sys.exit(1)

def start():
    import threading
    t = threading.Thread(target=base)
    t.setDaemon(True)
    t.start()
    print('Heart beat started')

if __name__ == '__main__':
    start()
    while True: pass
