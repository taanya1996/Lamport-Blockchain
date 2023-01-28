# Lamport-Blockchain

CMPSC 271 Programming assignment 1. 

For the implementation of Lamport Algorithm, it is essential to have TCP connection as we have to make sure that all the Lamport MUTEX request, reply and release has to be delivered to the peer clients and with the successful delivery of messages, the client can make decision to acquire the lock and perform the transaction. UDP doesn't guarantee the delivery. <br />

To run server:  <br />
python3 server.py  <br />

To run clients:  <br />
python3 client.py 1  <br />
python3 client.py 2  <br />
python3 client.py 3   <br />

The 3 clients and 1 server has to be simultaneously run in 4 different terminal.

