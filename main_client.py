# example of hart ip tcp recieving as client
#
import threading
import socket

from connections import ClientConnection

HART_IP_PORT = 5094
LISTEN_THREADS = 5

'''
program entry.
'''
def Main():
    c = ClientConnection((0, "192.1.2.1"))
    tcp_cli = c.connect_tcp_client()
    if not tcp_cli == -1:
        c.set_client(tcp_cli)
        c.run()
    
if __name__ == "__main__":
    Main()
