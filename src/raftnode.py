from commons import RPCPacket
from gevent.socket import SocketType

import commons
import gevent
import logging
import os
import sys
import time

LOGGER_NAME = "raftel-node"
logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(int(os.environ.get("raftel_log_level", logging.INFO)))

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

file_handler = logging.FileHandler("raftel-node.log")
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

class RaftNode(object):

    def __init__(self, election_timeout: int, wait_sleep: int =100) -> None:
        """
        election_timeout and wait_sleep are both specified as milliseconds.

        election_timeout is the time this node will wait for a leader heartbeat.
        Once elapsed, it will volunteer itself to be the leader.

        wait_sleep is the time this node sleeps between sending a keep alive to
        the RPC Overseer.
        """
        self.sock = SocketType()
        # "Mock" leader ping to start with.
        self.last_leader_ping = int(time.time() * 1000)
        self.election_timeout = election_timeout
        self.wait_sleep = wait_sleep

    def connect(self, ip: str, port: int) -> None:
        self.sock.connect((ip, port))
        login = RPCPacket(0, ord("A"))
        logger.info("SEND: %s" % login)
        self.sock.sendall(login.make_sendable_stream())
        spam = self.sock.recvfrom(128)
        
        logger.info("RECV: %s" % spam[0])

    def serve_forever(self) -> None:
        packet_number = 1
        while True:
            gevent.sleep(self.wait_sleep / 1000)
            # Send a keep alive
            keepalive = RPCPacket(packet_number=packet_number, command=ord("C"))
            logger.info("SEND: %s" % keepalive)
            self.sock.sendall(keepalive.make_sendable_stream())
            resp = self.sock.recvfrom(128)

            logger.info("RECV: %s" % resp[0])

if __name__ == "__main__":
    st = RaftNode(10, 4000)
    st.connect("127.0.0.1", int(sys.argv[1]))
    st.serve_forever()
