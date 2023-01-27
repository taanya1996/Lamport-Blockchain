import sys
import socket
import pickle
import heapq
import hashlib
import time

from threading import Thread, Lock
from common import *


HOST = "127.0.0.1"  # The server's hostname or IP address
SERVER_PORT = 65432  # The port used by the server
CLIENT_PORTS = [60001, 60002, 60003] # ports used by clients
CLIENT_RANGE=[1,2,3]
client_connections={}
requestPriorityQueue = [] 
transactionFlag = False
user_input = ""
buff_size=1024
replyCount=0
myClock=LamportClock(0,0)
BCHAIN=BlockChain()
reqClock = LamportClock(0,0)
lock=Lock()

class Connections(Thread):
    def __init__(self,connection):
        Thread.__init__(self)
        self.connection = connection
        

    def run(self):
        global replyCount
        global requestPriorityQueue
        global transactionFlag
        global myClock
        global reqClock
        
        while(True):
            response = self.connection.recv(buff_size)
            if not response:
                continue

            data = pickle.loads(response)
            
            #print("Current clock of process " + str(pid) + " is " + str(myClock))
            
            if data.reqType == "MUTEX":
                lock.acquire()
                #requestPriorityQueue.append(LamportClock(data.reqClock.clock, data.reqClock.pid))
                #heapq.heapify(requestPriorityQueue)
                print("REQUEST recieved from " + str(data.fromPid) + " at " + str(myClock))
                BCHAIN.insert(transaction=data.transaction, clock=data.clock)
                reqClock=data.clock
                sleep()
                print("REPLY sent to " + str(data.fromPid) + " at " + str(myClock))
                #print("Current clock of process " + str(pid) + " is " + str(myClock))
                reply = RequestMessage(pid, myClock, "REPLY")
                self.connection.send(pickle.dumps(reply))
                lock.release()
                
            if data.reqType == "REPLY":
                print("REPLY recieved from " + str(data.fromPid) + " at " + str(myClock))
                #print("MY CLOCK TIME Here is: ",str(myClock))
                sleep()
                lock.acquire()
                replyCount += 1
                print("replycount:", replyCount, " head_index:",BCHAIN.head_index, " SenderPID:", BCHAIN.data[BCHAIN.head_index].transaction.sender)
                if  BCHAIN.data[BCHAIN.head_index].transaction.sender ==  pid and replyCount == 2:
                    print("Acquired Lock")
                    '''
                    print("Local Queue:")
                    for i in range(BCHAIN.head_index, len(BCHAIN.data)):
                        print("CLOCK: {} Transaction: SENDER|RECEIVER|AMT : {}".format(BCHAIN.data[i].clock, BCHAIN.data[i].transaction))
                    print("Executing Transaction")
                       '''
                    self.handle_transaction()
                    #once the transaction is executed, lock should be released i.e move the head pointer
                    replyCount = 0
                    transactionFlag = True
                lock.release()

            if data.reqType == "RELEASE":
                print("RELEASE recieved from " + str(data.fromPid) + " at " + str(myClock))
                sleep()
                lock.acquire()
                BCHAIN.move()
                if BCHAIN.head_index!=-1 and BCHAIN.data[BCHAIN.head_index].transaction.sender ==  pid and replyCount == 2:
                    '''
                    print("Local Queue:")
                    for i in range(BCHAIN.head_index, len(BCHAIN.data)):
                        print("i", i)
                        print("CLOCK: {} Transaction: SENDER|RECEIVER|AMT : {}".format(BCHAIN.data[i].clock, BCHAIN.data[i].transaction))
                    print("Executing Transaction inside release")
                    '''
                    self.handle_transaction()
                    replyCount = 0
                    transactionFlag = True
                lock.release()
                
                    
                    
    def handle_transaction(self): 
        print("Handling transaction")
        transaction=BCHAIN.data[BCHAIN.head_index].transaction
        sleep()
        print("Requesting sender Balance from Server")
        request = RequestMessage(pid, myClock, "BALANCE")
        client_connections[0].sendall(pickle.dumps(request))
        balance = client_connections[0].recv(buff_size)
        balance= pickle.loads(balance)
        #myClock.incrementClock()
        sleep()
        print("======================================")
        print("Balance before transaction " + str(balance))
        print("======================================")

        if int(balance)>= int(transaction.amount):
            #continue with transaction
            request = RequestMessage(pid, myClock, "TRANSACTION", transaction)
            client_connections[0].sendall(pickle.dumps(request))
            trans_receipt= pickle.loads(client_connections[0].recv(buff_size))
            print("Transaction was " + str(trans_receipt))
            print("Balance after transaction is: ", int(balance)-int(transaction.amount))
            print("======================================")
            # to be filled here
        else:
            #abort the transaction
            print("Insufficient Balance, transaction Aborted")
            print("======================================")
        BCHAIN.move()
        broadcast("RELEASE", transaction=transaction, clock=myClock)

def sleep():
    time.sleep(3)
                    
            
class RequestMessage:
    def __init__(self, fromPid, clock=None, reqType=None, transaction=None, status=None):
        self.fromPid = fromPid
        self.clock = clock
        self.reqType = reqType
        self.transaction=transaction
        self.status = status
        
def sendRequest(client, reqType, clock=None, transaction=None, status=None):
    #myClock.incrementClock()
    #print("Current clock of process " + str(pid) + " is " + str(myClock))
    sleep()
    if reqType == "MUTEX":
        print("MUTEX REQUEST sent to " + str(client) + " at " + str(clock))
    elif reqType == "RELEASE":
        print("RELEASE sent to " + str(client) + " at " + str(clock))

    msg = RequestMessage(pid, clock, reqType, transaction, status)
    data_string = pickle.dumps(msg)
    client_connections[client].sendall(data_string) 


def closeSockets():
    client_connections[0].close()
    
    if pid == 1:
        client_connections[2].close()
        client_connections[3].close()
    elif pid == 2:
        client_connections[1].close()
        client_connections[3].close()
    elif pid == 3:
        client_connections[1].close()
        client_connections[2].close()    
            
def broadcast(reqType, transaction=None, status=None, clock=myClock):
    if pid == 1:
        sendRequest(2,reqType, clock, transaction, status)
        sendRequest(3,reqType, clock, transaction, status)
    elif pid == 2:
        sendRequest(1,reqType, clock, transaction, status)
        sendRequest(3,reqType, clock, transaction, status)
    elif pid == 3:
        sendRequest(1,reqType, clock, transaction, status)
        sendRequest(2,reqType, clock, transaction, status)
            


def main():
    global myClock
    global pid
    global user_input
    global myClock
    global reqClock
    global replyCount
    global transactionFlag
    global client_connections
    global BCHAIN

    client_id= int(input("enter client id in range [1,2,3]\n"))
    
    if(client_id not in CLIENT_RANGE):
        print("Enter valid client ID")
        return
    
    pid=client_id
    
    client_port=CLIENT_PORTS[client_id-1]
    print(client_port)
    
    c_socket = socket.socket()
    c_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    c_socket.bind((HOST, client_port))
    
    print("Initiating the connection to server")

    myClock = LamportClock(0,pid)

    try:
        c_socket.connect((HOST, SERVER_PORT))
        print("Connected to server")
    except socket.error as e:
        print(str(e))
        print("error connecting to server")
     
    #to accept from other clients
    client_connections[0]=c_socket
    
    if(client_id==1):
                                       
        #connection should be from 1,2
        
        c2c = socket.socket()
        c2c.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        c2c.bind((HOST, 60010))
        c2c.listen(2)
        
        conn, addr= c2c.accept()
        print('Connected to Client 2: ' + addr[0] + ':' + str(addr[1]))
        client_connections[2]=conn
        new_client = Connections(conn)
        new_client.start()
                           
             
        conn, addr= c2c.accept()
        print('Connected to Client 3: ' + addr[0] + ':' + str(addr[1]))
        client_connections[3]=conn
        new_client = Connections(conn)
        new_client.start()
                           
                           
    if(client_id==2):
        
        c2c = socket.socket()
        c2c.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        c2c.bind((HOST, 60020))

        try:
            c2c.connect((HOST, 60010))
            print('Connected to Client 1: ' + HOST + ':' + str(60010))
        except socket.error as e:
            print(str(e))
            print("error connecting to client1")
                           
         
        client_connections[1] = c2c
        new_connection = Connections(c2c)
        new_connection.start()

        c2c = socket.socket()
        c2c.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        c2c.bind((HOST, 60020))
        c2c.listen(2)

        
        
        conn, addr= c2c.accept()
        print('Connected to Client 3: ' + addr[0] + ':' + str(addr[1]))
        client_connections[3]=conn
        new_client1 = Connections(conn)
        new_client1.start()
       
        
                           
    if(client_id==3):
        
        c2c = socket.socket()
        c2c.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        c2c.bind((HOST, 60030))

        try:
            c2c.connect((HOST, 60010))
            print('Connected to Client 1: ' + HOST + ':' + str(60010))
        except socket.error as e:
            print(str(e))
            print("error connecting to client1")

        client_connections[1] = c2c
        new_connection = Connections(c2c)
        new_connection.start()

        c2c = socket.socket()
        c2c.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        c2c.bind((HOST, 60030))

        try:
            c2c.connect((HOST, 60020))
            print('Connected to Client 2: ' + HOST + ':' + str(60020))
        except socket.error as e:
            print(str(e))
            print("error connecting to client2")

        client_connections[2] = c2c
        new_connection1 = Connections(c2c)
        new_connection1.start()
        
    print("=======================================================")
    print("Current Balance is $10")

    while True:
        transactionFlag = False
        print("=======================================================")
        print("| For Balance type 'BAL'                              |")
        print("| For transferring money - RECV_ID AMOUNT Eg.(2 5)    |")
        print("| For chain type : 'BLOCKCHAIN'                       |")
        print("| To quit type 'Q'                                    |") 
        print("=======================================================")
        user_input = input()

        if user_input != "Q" and user_input != "BAL" and user_input!="BLOCKCHAIN" and len(user_input.split()) != 2:
            print("Please enter valid input")
            continue

        if user_input == "Q":
            break
        
        if user_input == "BLOCKCHAIN":
            #print BlockChain here
            BCHAIN.print()
            continue

        if user_input== 'BAL':
            request = RequestMessage(pid,None,"BALANCE")
            #sleep()
            print("Balance request sent to server")
            #print("Current clock of process " + str(pid) + " is " + str(myClock))
            client_connections[0].sendall(pickle.dumps(request))
            balance = client_connections[0].recv(buff_size)        
            balance= pickle.loads(balance)
            
            print("=============================")
            print("Balance is " + str(balance))
            print("=============================")
            #transactionFlag = True  

        else:
            # its transaction 
            myClock.updateClock(reqClock)
            sender=pid
            receiver, amt= [int(x) for x in user_input.split()]
            print("Trying to get the Mutex!!!")

            print("Current clock of process " + str(pid) + " is " + str(myClock))
            transaction=Transaction(sender,receiver,amt)
            print("Transaction", transaction)
            replyCount = 0
            # is insert happening correctly
            BCHAIN.insert(transaction=transaction, clock=myClock.copy())
            # good to send clock from here only
            broadcast("MUTEX", transaction=transaction, clock=myClock.copy())
            while transactionFlag == False:
                time.sleep(1)
        
    closeSockets()

if __name__ == "__main__":
    main()
    
