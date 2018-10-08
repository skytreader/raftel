from argparse import ArgumentParser
from commons import RPCPacket
from gevent.socket import SocketType

import commons
import gevent
import logging
import os
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
    parser = ArgumentParser(description="node for a raft cluster")
    parser.add_argument(
        "--election-timeout", "-e", required=False, type=int, default=10,
        help="How long to wait for a leader heartbeat. Measured in milliseconds."
    )
    parser.add_argument(
        "--keep-alive", "-k", required=False, type=int, default=30000,
        help="The time between keep-alives to the RPC overseer. Measured in milliseconds."
    )
    parser.add_argument(
        "--host", "-H", required=True, type=str,
        help="The host address of the RPC overseer."
    )
    parser.add_argument(
        "--port", "-p", required=True, type=int,
        help="The port on which the RPC overseer is listening."
    )

    args = vars(parser.parse_args())

    st = RaftNode(args["election_timeout"], args["keep_alive"])
    st.connect(args["host"], args["port"])
    st.serve_forever()
