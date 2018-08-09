from gevent.server import StreamServer
from commons import RPCPacket

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
"""

LOGGER_NAME = "raftel-overseer"
logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(os.environ.get("raftel-log-level", logging.INFO))

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

file_handler = logging.FileHandler("raftel-overseer.log")
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

class OverSeerver(StreamServer):

    def __init__(self, bind_port, **kwargs):
        super(OverSeerver, self).__init__(("127.0.0.1", bind_port))
        self.leader = None
        self.socket_clique = []

    def __interpret_command(self, packet):
        parsed_packet = RPCPacket.parse(packet, logger_name=LOGGER_NAME)
        logger.debug("The command is %s vs %s" % (parsed_packet.command, ord('A')))
        if parsed_packet.command == b'A':
            return bytes([
                commons.STX, int.from_bytes(parsed_packet.packet_number, sys.byteorder),
                commons.RS, commons.ACK, commons.ETX
            ])

    def handle(self, client_socket, address):
        logger.info("connection RECV %s" % client_socket)
        packet_acc = []

        while commons.ETX not in packet_acc:
            p = client_socket.recvfrom(32)
            logger.debug(p)
            packet_acc.extend(p[0])
        
        logger.info("RECV %s" % packet_acc)
        resp = self.__interpret_command(packet_acc)
        logger.info("SEND %s" % resp)
        client_socket.sendall(resp)

if __name__ == "__main__":
    overseer = OverSeerver(int(sys.argv[1]))
    overseer.serve_forever()
