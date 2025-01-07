# example of hart ip server
#
import threading
import socket

from connections import ServerConnection

HART_IP_PORT = 5094
LISTEN_THREADS = 5

'''
program entry.
'''
def Main():
    s = ServerConnection(HART_IP_PORT, LISTEN_THREADS)
    s.run_tcp()
    #s.run_udp() - for udp packets
    
if __name__ == "__main__":
    Main()
