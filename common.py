import hashlib

class RequestMessage:
    def __init__(self, fromPid, clock, reqType, reqClock = None, block = None):
        self.fromPid = fromPid
        self.clock = clock
        self.reqType = reqType
        self.reqClock = reqClock
        self.block = block

class LamportClock:
    def __init__(self, clock, pid):
        self.clock = clock
        self.pid = pid

    def incrementClock(self):
        self.clock += 1
    
    def copy(self):
        return LamportClock(self.clock, self.pid)

    def __lt__(self, other):
        if self.clock < other.clock:
            return True
        elif self.clock == other.clock:
            if self.pid < other.pid:
                return True
            else:
                return False
        else:
            return False

    def updateClock(self, clock):
        self.clock = max(self.clock, clock.clock) + 1

    def __str__(self):
        return str(self.clock) + "." + str(self.pid)

class Transaction:
	def __init__(self, sender, receiver, amount):
		self.sender = sender
		self.receiver = receiver
		self.amount = amount

	def __str__(self):
		return str(self.sender) + "|" + str(self.receiver) + "|" + str(self.amount)


class Block:
    def __init__(self, headerHash, transaction, clock, status=""):
        self.headerHash = headerHash
        self.transaction = transaction
        self.clock = clock
        self.status = status

    def status_update(self,status):
        self.status=status

    def __str__(self):
        return str(self.headerHash) + "| " + str(self.transaction) + " | " + str(self.status) + " | " + str(self.clock)

class BlockChain:
    def __init__(self):
        self.data=[]
        self.length=0
        self.head_index=-1

    def updateBlockChain(self, pos):
        for i in range(pos, self.length):
            prevHashData="" if pos==0 else str(self.data[pos-1])
            headerHash = hashlib.sha256(prevHashData.encode()).digest()
            self.data[i].headerHash=headerHash

    def move(self):
        print("Moving the header from sender ",  self.data[self.head_index].transaction.sender)
        print("Header prev at {}".format(self.head_index))
        self.head_index+= 1

        if(self.head_index>=self.length):
            self.head_index=-1
        
        print("Header now is at {}".format(self.head_index))
        #some issue, please check

    def insertBLOCK(self, transaction, clock):
        if self.head_index==-1:
            prevHashdata="" if self.length==0 else str(self.data[self.length-1])
            headerHash=hashlib.sha256(prevHashdata.encode()).digest()
            block= Block(headerHash, transaction, clock)
            self.data.append(block)
            self.length+=1
            self.head_index=self.length-1
            print(str(block))
            return
        
        pos_ind=self.head_index
        block = Block("", transaction, clock)
        # to check if the priority of the new block is higher than head
        print("Len of BlockChain:",len(self.data))
        for i in range(self.head_index,-1,-1):
            print("i,head_index",i,self.head_index)
            if clock < self.data[i].clock:
                pos_ind-=1
                self.head_index=pos_ind+1
            else:
                break
        for i in range(self.head_index+1,self.length):
            if self.data[i].clock < clock:
                pos_ind+=1
            else:
                break
        self.length+=1
        self.data.insert(pos_ind+1,block)
        self.updateBlockChain(pos_ind+1)
        print("Header now is at {}".format(self.head_index))

    def insert(self, transaction, clock):
        self.insertBLOCK(transaction, clock)
    
    def print(self):
        print("======================================")
        print("Total of {} nodes in blockchain".format(self.length))
        for block in self.data:
            print(str(block))
        print("======================================")
