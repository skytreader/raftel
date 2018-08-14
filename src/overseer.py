from gevent.server import StreamServer
from commons import RPCPacket
from typing import List

import commons
import logging
import os
import sys

"""
The Overseer protocol is a RS-delimited (byte 1E) protocol which follows the
following guidelines. This is the RPC router/mechanism between raftel nodes:

- All transmissions are wrapped around STX (2) and ETX (3) bytes. Immediately
after the STX, is the packet number which is eight bits (so wrap around 256).
After that is the command.

- Commands (between STX and ETX) follow the format <command><RS><args...>
where arguments are also RS delimited.

# Reserved instructions for Overseer.

- Responses will have either ACK or NACK for their commmand field.

- Responses will take the form <ACK OR NACK><RS><ADDITIONAL INFO>.

- Every command will be ACKed (6) or NACKed (15), depending on whether the
transaction is successful or not. NACKs will give the following reasons:
    
    Z - General failure
    Y - Malformed packet, please retransmit.
    X - Invalid/unknown command.

Responses will also start with the packet number they are acknowledging.

- When a client connects to the Overseer, it connects with a log-in command (A).

- Graceful termination would happen by sending a log-out command (B).

- During idle times, each node should send a keep alive (C) to the Overseer.
This is distinct from the leader heartbeat specified in the Raft protocol.
"""

LOGGER_NAME = "raftel-overseer"
logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(int(os.environ.get("raftel_log_level", logging.INFO)))

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

file_handler = logging.FileHandler("raftel-overseer.log")
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

class OverSeerver(StreamServer):

    def __init__(self, bind_port: int, **kwargs) -> None:
        super(OverSeerver, self).__init__(("127.0.0.1", bind_port))
        self.leader = None
        self.socket_clique = [] # type: list

    def __make_response(self, parsed_packet: RPCPacket) -> RPCPacket:
        logger.debug("The command is %s vs %s" % (parsed_packet.command, ord('A')))
        if parsed_packet.validate():
            logger.debug("Calling RPCPacket for ACK")
            ack = RPCPacket(parsed_packet.packet_number, commons.ACK)
            return ack

    def handle(self, client_socket, address):
        logger.info("connection RECV %s" % client_socket)
        packet_acc = [] # type: List[int]

        while commons.ETX not in packet_acc:
            p = client_socket.recvfrom(32)
            logger.debug(p)
            packet_acc.extend(p[0])
        
        parsed_packet = RPCPacket.parse(packet_acc)
        logger.info("RECV %s" % parsed_packet)
        resp = self.__make_response(parsed_packet)
        if parsed_packet.command == ord("A") and resp.command == commons.ACK:
            self.socket_clique.append(client_socket)
        logger.info("SEND %s" % resp)
        client_socket.sendall(resp.make_sendable_stream())

if __name__ == "__main__":
    overseer = OverSeerver(int(sys.argv[1]))
    logger.info("Starting overseer...")
    overseer.serve_forever()
