#!/usr/bin/env python3
import socket, sys, time

def heart_beat():
    HOST = '' # Your remote server IP
    PORT = 2010 # Your remote server port
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
            time.sleep(60) # Set your heart beat delay, 1 min is recommended.
        except KeyboardInterrupt:
            sys.exit(1)

if __name__ == '__main__':
    print('Start heart beat...')
    heart_beat()
