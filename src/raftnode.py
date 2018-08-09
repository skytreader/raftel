from commons import RPCPacket
from gevent.socket import SocketType

import commons
import logging
import os
import time

LOGGER_NAME = "raftel-node"
logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(os.environ.get("raftel-log-level", logging.INFO))

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

file_handler = logging.FileHandler("raftel-node.log")
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

class RaftNode(object):

    def __init__(self, election_timeout):
        self.sock = SocketType()
        # "Mock" leader ping to start with.
        self.last_leader_ping = int(time.time() * 1000)
        self.election_timeout = election_timeout

    def connect(self, ip, port):
        self.sock.connect((ip, port))
        login = RPCPacket(0, ord("A"))
        logger.info("SEND: %s" % login)
        self.sock.sendall(login.make_sendable_stream())
        spam = self.sock.recvfrom(128)
        
        logger.info("RECV: %s" % spam[0])

if __name__ == "__main__":
    st = RaftNode(10)
    st.connect("127.0.0.1", 16981)
