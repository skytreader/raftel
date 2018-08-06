from gevent.socket import SocketType

import time

class RaftNode(SocketType):

    def __init__(self, election_timeout):
        self.sock = SocketType()
        # "Mock" leader ping to start with.
        self.last_leader_ping = int(time.time() * 1000)
        self.election_timeout = election_timeout

    def connect(self, ip, port):
        self.sock.connect((ip, port))

if __name__ == "__main__":
    st = SocketType()
    st.connect(("127.0.0.1", 16981))
