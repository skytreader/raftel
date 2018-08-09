from gevent.socket import SocketType

import commons
import time

class RaftNode(object):

    def __init__(self, election_timeout):
        self.sock = SocketType()
        # "Mock" leader ping to start with.
        self.last_leader_ping = int(time.time() * 1000)
        self.election_timeout = election_timeout

    def connect(self, ip, port):
        self.sock.connect((ip, port))
        login = bytes([
            commons.STX, 0, commons.RS, ord("A"), commons.ETX
        ])
        self.sock.sendall(login)
        spam = self.sock.recvfrom(128)
        
        print(spam)

if __name__ == "__main__":
    st = RaftNode(10)
    st.connect("127.0.0.1", 16981)
