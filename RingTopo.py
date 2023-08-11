from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel, output, info
import os
import time
import random
import networkx as nx

def ringNet(N):
    net = Mininet(controller=Controller)

    info("Adding hosts" + "\n")          #h1 = net.addHost('h1')
    #N = int(N)
    host_list = []
    for host in range(1,N+1):
        host_list.append("h" + str(host))
    print(host_list)

    info("Adding switches" + "\n")      #s1 = net.addSwitch('s1')
    switch_list = []
    for switch in range(1,N+1):
        switch_list.append("s" + str(switch))
    print(switch_list)

    info("Creating links" + "\n")   #net.addLink(h1,s1)
    for i in range(1,N):
        print(i)
        host_list[i] = net.addHost("h" + str(i))
        switch_list[i] = net.addSwitch("s" + str(i))
        net.addLink (host_list[i], switch_list[i])

    for index in range(1, len(switch_list)):
         for index2 in range(index+1, len(switch_list)):    #len(switch_list)
            net.addLink(switch_list[index], switch_list[index2])
    #net.addLink(switch_list[N], switch_list[1])

def hostRand(N):
    G = nx.Graph()
    myFalseEdges = []
    nodes = [i for i in range(1, N+1)]
    for i in range(1,20):
        s = random.choice(nodes)
        t = random.choice(nodes)
        if t != s:
            print(str(s),"<->",str(t))
            if not (t in sorted(nx.all_neighbors(G,s))):
                print("can use this one!")
                if not (tuple(sorted((s,t))) in myFalseEdges):
                    myFalseEdges.append(tuple(sorted((s,t))))

    (host1, host2) = random.choice(MyFalseEdges)
    print(host1)
    print(host2)
    return (host1,host2)

def UDPCS1():
    #load_contrib('lldp')
    h1 = net.getNodeByName("h1")
    h3 = net.getNodeByName("h3")

    # Create a datagram socket
    print("Host-Based attack start")
    h1.cmd('python3 UDPServerH1.py &')
    h3.cmd('python3 UDPServerH3.py &')

    print("Host-Based attack from client")
    h3.cmd('python3 UDPClientH3.py &')
    h1.cmd('python3 UDPClientH1.py &')

def HostAttack(self,line):
    #TestRTT1()
    UDPCS1()

if __name__ == '__main__':
    os.system("mn -c > /dev/null 2>&1")   
    setLogLevel('info')
    
    topo = ringNet(15)
    net = Mininet( topo=topo,
                   link=TCLink,
                   controller=Controller)

    info("Adding controller" + "\n")
    net.addController('c0', controller=RemoteController)

    net.start()

    CLI.do_HostAttack = HostAttack
    
    info("enter \"quit\" to exit or issue mininet commands if you know them" +  "\n")
    info("you can run the tests using the commands \"HostAttack\" or \"\" ...." +  "\n")
    
    CLI
    net.stop()
