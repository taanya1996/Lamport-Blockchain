import socket
import pickle
import os
import hashlib
import time

from threading import Thread
from common import *

BALANCE_SHEET = {1:10,2:10,3:10}
HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
SERVER_PORT = 65432  # Port to listen on (non-privileged ports are > 1023)
CLIENT_PORTS = [60001, 60002, 60003]
CLIENT_CONNECTIONS = {}
BUFFER_SIZE = 1024
BALANCE = "BAL"
QUIT = "Q"


class Server_Thread(Thread):
    def __init__(self,connection,host,port,pid):
        Thread.__init__(self)
        self.connection = connection
        self.host = host
        self.port = port
        self.pid=pid

    def run(self):
        self.handle_messages()        
        self.connection.close()

    def handle_messages(self):
        print("Server is handing the message now: Inside Handle message")
        while True:
            try:
                request = self.connection.recv(BUFFER_SIZE)
            except:
                print("Closing the connection for Client {}".format(self.pid))
                break
            if not request:
                continue
                
            data = pickle.loads(request)
            
            if data.reqType == "BALANCE":
                self.get_balance(data)
            elif data.reqType == "TRANSACTION":
                self.add_transaction(data)
    
    def get_balance(self, data):
        global BALANCE_SHEET
        print("Sending the balance to Client {} as {}".format(data.fromPid, BALANCE_SHEET[data.fromPid]))
        CLIENT_CONNECTIONS[data.fromPid].connection.sendall(pickle.dumps(BALANCE_SHEET[data.fromPid]))

    def add_transaction(self, data):
        global BALANCE_SHEET
        global CLIENT_CONNECTIONS
        print("Adding a transaction of {} $ from Client {} to Client {}".format(data.transaction.amount,
                                    data.transaction.sender, data.transaction.receiver))
        try:
            BALANCE_SHEET[data.transaction.sender] -= data.transaction.amount
            BALANCE_SHEET[data.transaction.receiver] += data.transaction.amount
            print("balance sheet successfully updated")
            CLIENT_CONNECTIONS[data.fromPid].connection.sendall(pickle.dumps("SUCCESS"))
        except:
            print("balance sheet successfully updated, but some issue in request code")
            CLIENT_CONNECTIONS[data.fromPid].connection.sendall(pickle.dumps("ABORT"))
               
        
def printBalance():
    global BALANCE_SHEET
    print("=========================================")
    for pid in BALANCE_SHEET:
        print("Client {} : {}".format(pid, BALANCE_SHEET[pid]))
    print("=========================================")
    

def main():
    global BALANCE_SHEET
    server_socket = socket.socket()
    try:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, SERVER_PORT))

    except socket.error as e:
        print(str(e))
    

    print("Server is now listening on Port 65432")
    server_socket.listen()
    client_count = 0
    
    while(client_count<len(CLIENT_PORTS)):
        conn, addr=server_socket.accept()
        print('Connected to: ' + addr[0] + ':' + str(addr[1]))
        client_count+=1
        pid = addr[1]%6000
        n_client= Server_Thread(conn, addr[0] , addr[1], pid)
        n_client.start()
        CLIENT_CONNECTIONS[pid] = n_client
        
    print("==============================================================")
    print("| For Balance type : '{}'                                   |".format(BALANCE))
    print("| To quit type : '{}'                                         |".format(QUIT)) 
    print("==============================================================")
    while True:
        print("===== Enter a command to compute =====")
        user_input = input()
        if user_input == BALANCE:
            printBalance()
        elif user_input == QUIT:
            server_socket.close()
            for connection in CLIENT_CONNECTIONS.values():
                connection.connection.close()
            break
            
    
            
if __name__ == "__main__":
    main()
