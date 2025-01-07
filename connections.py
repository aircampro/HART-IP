import socket
import threading
import time
from hartip import ReceiveFromSocket
from pprint import pprint
import sys

REC_BUFFER_SIZE = 2048
HART_IP_PORT = 5094

class ServerConnection():
    '''
    initiate
    '''
    def __init__(self,port,threads):
        self.host    = ''
        self.port    = port
        self.threads = threads        

    def __del__(self):
        self.server.close()
		
    '''
    TCP Server
    '''
    def open_socket_with_TCP(self): 
        try: 
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
            self.server.bind((self.host,self.port)) 
            self.server.listen(self.threads) 
        except socket.error, (value,message): 
            if self.server: 
                self.server.close() 
            pprint("Could not open socket: %s" % message) 
            sys.exit(1) 
    
    '''
    UDP Server
    '''
    def open_socket_with_UDP(self): 
        try: 
            self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server.bind((self.host,self.port)) 
            self.server.listen(5) 
        except socket.error, (value,message): 
            if self.server: 
                self.server.close() 
            pprint("Could not open socket: %s" % message) 
            sys.exit(1)             
  
    '''
    inspect the ip address is ipv4 or not
    '''
    def is_valid_ipv4_address(self,address):
        try:
            addr= socket.inet_pton(socket.AF_INET, address)
        except AttributeError: # no inet_pton here, sorry
            try:
                addr= socket.inet_aton(address)
            except socket.error:
                return False
            return address.count('.') == 3
        except socket.error: # not a valid address
            return False
        return True
    
    '''
    inspect the ip address is ipv6 or not
    '''
    def is_valid_ipv6_address(self,address):
        try:
            addr= socket.inet_pton(socket.AF_INET6, address)
        except socket.error: # not a valid address
            return False
        return True
    
    '''
    initiate the socket connection,and start the listenning thread
    '''
    def run_tcp(self):
        self.open_socket_with_TCP()
        while True:
            c = ClientConnection(self.server.accept())
            pprint("%s %s" % ( c.client,c.addr))
            c.start()
    
    def run_udp(self)
        self.open_socket_with_TCP()
        while True:
            c = ClientConnection(self.server.accept())
            pprint("%s %s" % (c.client,c.addr))
            c.start()    
    
class ClientConnection(threading.Thread):
    '''
    client:socket.accept return the socket connection
    addr  :socket.accept return the source address
    '''
    def __init__(self,(client,addr)):
        threading.Thread.__init__(self)
        self.client      = client
        self.addr        = addr
        self.size        = REC_BUFFER_SIZE
        self.timeoutcnt  = 0
        self.timeoutval  = 180 

    def __del__(self):
        self.client.close()
		
    # returns a tcp client connection handle
    def connect_tcp_client(self, port=HART_IP_PORT):
        TCP_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   
        TCP_client.settimeout(10)
        try:
            TCP_client.connect((self.addr, port))
            return TCP_client
        except socket.error:
            TCP_client.close()
            return -1

    # returns a udp client connection handle    
    def connect_udp_client(self, port=HART_IP_PORT):
        UDP_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   
        UDP_client.settimeout(10)   
        try:
            UDP_client.connect((self.addr, port))
            return UDP_client
        except socket.error:
            UDP_client.close()
            return -1

    # reconfigures the client connection to use the handle returned from either function call above
    def set_client(self, client):
        self.client = client
		
    '''
    ovrerride the run method
    '''
    def run(self):
        while True:
            try:
                rec_data = self.client.recv(self.size)
                if sys.version_info.major == 3:
                    rec_data = rec_data.decode('utf-8')
                ReceiveFromSocket(rec_data,self.client)
                if not rec_data: break
            except Exception as e:
                pprint(e)                
                self.client.close() 
                break
        pprint('over')
        self.client.close()
