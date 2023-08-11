import socket
import time
from scapy.all import *
from threading import Thread
from queue import Queue

load_contrib('lldp')

#localIP     = "0.0.0.0"
#localPort   = 20001
#bufferSize  = 1024
msgFromServer       = "Hello UDP Client"
bytesToSend         = str.encode(msgFromServer)

# Create a datagram socket
UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

# Bind to address and ip
UDPServerSocket.bind(("0.0.0.0", 20001))
print("UDP server up and listening")

# Listen for incoming datagrams
while(True):
    bytesAddressPair = UDPServerSocket.recvfrom(1024)
    message = bytesAddressPair[0]
    address = bytesAddressPair[1]

    clientIP  = "Client IP Address:{}".format(address)
    print(clientIP)

    clientMsgLen = "Message len from Client:{}".format(len(message))
    print(clientMsgLen)
    pack = Ether(message)
    #pack.show()
    
    # Sending a reply to client
    #UDPServerSocket.sendto(bytesToSend, address)
    sendp(pack, loop=0, verbose=1, iface="h3-eth0")
    #time.sleep(500)