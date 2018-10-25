from argparse import ArgumentParser
from commons import RPCPacket, OverseerCommands
from enum import Enum
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

class NodeStates(Enum):
    FOLLOWER = 0
    CANDIDATE = 1
    LEADER = 2

class RaftNode(object):

    def __init__(self, election_timeout: int, wait_sleep: int =100) -> None:
        """
        election_timeout and wait_sleep are both specified as milliseconds.

        election_timeout is the time this node will wait for a leader heartbeat.
        Once elapsed, it will volunteer itself to be the leader.

        wait_sleep is the time this node sleeps between sending a keep alive to
        the RPC Overseer.

        You typically want election_timeout to be greater than wait_sleep. The
        rationale is that you want the node to send a few keep alives to
        overseer before trying to go for election; this gives the other nodes
        time to join the cluster.
        """
        self.sock = SocketType()
        # "Mock" leader ping to start with.
        self.last_leader_ping = self.__current_time_millis() # type: int
        self.last_transaction = self.__current_time_millis() # type: int
        self.election_timeout = election_timeout # type: int
        self.wait_sleep = wait_sleep # type: int

        self.current_term = 0 # type: int
        self.state = NodeStates.FOLLOWER # type: NodeStates

    def __current_time_millis(self) -> int:
        return int(time.time() * 1000)

    def connect(self, ip: str, port: int) -> None:
        self.sock.connect((ip, port))
        login = RPCPacket(0, OverseerCommands.LOGIN.value)
        logger.info("SEND: %s" % login)
        self.sock.sendall(login.make_sendable_stream())
        overseer_resp = self.sock.recvfrom(128)
        logger.info("RECV: %s" % overseer_resp[0])
        parse_resp = RPCPacket.parse(overseer_resp[0])
        logger.info("Got client id %s" % parse_resp.additional_info)
        self.last_transaction = self.__current_time_millis()

    def serve_forever(self) -> None:
        packet_number = 1
        while True:
            now = self.__current_time_millis()
            send_packet = None # type: RPCPacket
            if (now - self.last_leader_ping) > self.election_timeout and self.state == NodeStates.FOLLOWER:
                # Tell the overseer you want to be the leader
                send_packet = RPCPacket(packet_number=packet_number, command=ord("D"))
                self.current_term += 1
                self.state = NodeStates.CANDIDATE
            else:
                # Send a keep alive
                keep_alive_diff = now - self.last_transaction
                if keep_alive_diff >= self.wait_sleep:
                    send_packet = RPCPacket(packet_number=packet_number, command=ord("C"))
                else:
                    gevent.sleep((self.wait_sleep - keep_alive_diff) / 1000)
                    send_packet = RPCPacket(packet_number=packet_number, command=ord("C"))
            
            logger.info("SEND: %s" % send_packet)
            self.sock.sendall(send_packet.make_sendable_stream())
            resp = self.sock.recvfrom(128)

            logger.info("RECV: %s" % resp[0])
            if not len(resp[0]):
                break
            self.last_transaction = self.__current_time_millis()

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
