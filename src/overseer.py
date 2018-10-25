from argparse import ArgumentParser
from commons import RPCPacket, OverseerCommands
from gevent import Greenlet, monkey
from gevent.server import StreamServer
from typing import List

import commons
import gevent
import logging
import os

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
The acknowledgement will return the candidate id in the additional info section.

- Graceful termination would happen by sending a log-out command (B).

- During idle times, each node should send a keep alive (C) to the Overseer.
This is distinct from the leader heartbeat specified in the Raft protocol.

# Raft-specific commands

Note that these are commands received by the overseer, for propagation.

D - Request Vote
"""

monkey.patch_all()

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

class ClientHandler(Greenlet):

    def __init__(self, client_socket: gevent._socket3.socket) -> None:
        Greenlet.__init__(self)
        self.client_socket = client_socket

    def __make_response(self, parsed_packet: RPCPacket) -> RPCPacket:
        if parsed_packet.validate():
            logger.debug("Calling RPCPacket for ACK")
            ack = RPCPacket(parsed_packet.packet_number, commons.ACK)
            return ack

    def __read_from_client(self, client_socket: gevent._socket3.socket, _packet_acc=None) -> List[int]:
        packet_acc = _packet_acc if _packet_acc else [] # type: List[int]

        while commons.ETX not in packet_acc:
            p = client_socket.recvfrom(32)
            logger.debug("Raw RECV from socket: %s" % str(p))
            if not len(p[0]):
                logger.critical("Received nothing from socket %s, breaking read loop..." % self.client_socket)
                break
            packet_acc.extend(p[0])
            gevent.sleep(0.5)

        return packet_acc

    def _run(self):
        while True:
            logger.debug("Reading from socket...")
            recv = RPCPacket.parse(self.__read_from_client(self.client_socket))
            logger.info("RECV %s" % recv)
            resp = self.__make_response(recv)
            logger.info("SEND %s" % resp)
            self.client_socket.sendall(resp.make_sendable_stream())
            gevent.sleep(1)

class OverSeerver(StreamServer):

    def __init__(self, bind_port: int, **kwargs) -> None:
        super(OverSeerver, self).__init__(("127.0.0.1", bind_port))
        self.leader = None
        self.socket_clique = [] # type: list
        # In Java-speak, this member should be synchronized.
        self.client_id = 1

    def __make_response(self, parsed_recv: RPCPacket) -> RPCPacket:
        if parsed_recv.validate():
            logger.debug("Calling RPCPacket for ACK")
            ack = RPCPacket(parsed_recv.packet_number, commons.ACK)

            # Add additional_info that might be relevant
            if parsed_recv.command == OverseerCommands.LOGIN:
                ack.additional_info = [self.client_id]
                self.client_id += 1
            return ack

    def __read_from_client(self, client_socket: gevent._socket3.socket, _packet_acc=None) -> List[int]:
        packet_acc = _packet_acc if _packet_acc else [] # type: List[int]

        while commons.ETX not in packet_acc:
            # TODO Refactor this with ClientHandler above.
            p = client_socket.recvfrom(32)
            logger.debug(p)
            if not len(p[0]):
                logger.critical("Client pinged but did not complete initial handshake.")
                break
            packet_acc.extend(p[0])

        return packet_acc

    def handle(self, client_socket: gevent._socket3.socket, address):
        logger.info("connection RECV %s" % client_socket)
        packet_acc = self.__read_from_client(client_socket) # type: List[int]
        
        parsed_packet = RPCPacket.parse(packet_acc)
        logger.info("RECV %s" % parsed_packet)
        resp = self.__make_response(parsed_packet)
        if parsed_packet.command == OverseerCommands.LOGIN and resp.command == commons.ACK:
            self.socket_clique.append(client_socket)
        logger.info("SEND %s" % resp)
        logger.info("Spawning greenlet for %s" % client_socket)
        client_socket.sendall(resp.make_sendable_stream())
        ch = ClientHandler(client_socket)
        ch.start()
        ch.join()
        gevent.sleep()
        logger.info("Killing greenlet %s" % client_socket)
        ch.kill()
        logger.info("Greenlet %s dead" % client_socket)

if __name__ == "__main__":
    parser = ArgumentParser(description="An RPC overseer for facilitating RAFT.")
    parser.add_argument(
        "--port", "-p", required=True, type=int,
        help="The port to which the overseer will bind and listen for connections."
    )
    args = vars(parser.parse_args())
    overseer = OverSeerver(args["port"])
    logger.info("Starting overseer...")
    overseer.serve_forever()
