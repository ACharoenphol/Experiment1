from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, Controller
from mininet.cli import CLI
#from mininet.log import setLogLevel, info
from mininet.log import setLogLevel, output, info
import os
import time
import random
import networkx as nx

def emptyNet(N):
    "Create an empty network and add nodes to it."
    net = Mininet(controller=Controller)

    info("Adding controller" + "\n")
    #net.addController('c0')
    #net.addController('c0', controller=RemoteController, ip="172.0.0.1", port=6633)

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

    info("Creating links" + "\n")
    for i in range(1,N):
        print(i)
        host_list[i] = net.addHost("h" + str(i))
        switch_list[i] = net.addSwitch("s" + str(i))
        net.addLink (host_list[i], switch_list[i])

    for index in range(1, len(switch_list)):
         for index2 in range(index+1, len(switch_list)):    #len(switch_list)
            net.addLink(switch_list[index], switch_list[index2])
    #net.addLink(switch_list[N], switch_list[1])

    #        print(j)
    #        net.addLink(switch_list[i], switch_list[j])
    #net.addLink(h1,s1)
    #net.addLink(h2,s3)
    #switchList = (s1,s2,s3,s4)
    #for index in range(0,len(switch_list)):
    
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
    
    net.start()
    CLI
    net.stop()

if __name__ == '__main__':
    os.system("mn -c > /dev/null 2>&1")   
    setLogLevel('info')
    emptyNet(15)
