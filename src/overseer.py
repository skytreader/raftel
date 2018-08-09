from gevent.server import StreamServer
import commons
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

class RPCPacket(object):

    def __init__(self, packet_number=None, command=None, additional_info=None):
        self.packet_number = packet_number
        self.command = command
        self.additional_info = additional_info

    @staticmethod
    def parse(packet_stream):
        byte_acc = []

        packet_order = ("packet_number", "command", "additional_info")
        packet_kwargs = {}
        field_index = 0

        # Automagically ignore STX and ETX
        i = 1
        limit = len(packet_stream) - 1

        while i < limit:
            print("inspecting: %s" % packet_stream[i])
            if packet_stream[i] == commons.RS and field_index < 2:
                packet_kwargs[packet_order[field_index]] = bytes(byte_acc)
                byte_acc = []
                field_index += 1
            else:
                byte_acc.append(packet_stream[i])
            i += 1

        packet_kwargs[packet_order[field_index]] = bytes(byte_acc)
        parsed_packet = RPCPacket(**packet_kwargs)
        return parsed_packet

class OverSeerver(StreamServer):

    def __init__(self, bind_port, **kwargs):
        super(OverSeerver, self).__init__(("127.0.0.1", bind_port))
        self.leader = None
        self.socket_clique = []

    def __interpret_command(self, packet):
        parsed_packet = RPCPacket.parse(packet)
        print("The command is %s vs %s" % (parsed_packet.command, ord('A')))
        if parsed_packet.command == b'A':
            return bytes([
                commons.STX, int.from_bytes(parsed_packet.packet_number, sys.byteorder),
                commons.RS, commons.ACK, commons.ETX
            ])

    def handle(self, client_socket, address):
        print("someone connected %s" % client_socket)
        packet_acc = []

        while commons.ETX not in packet_acc:
            p = client_socket.recvfrom(32)
            print(p)
            packet_acc.extend(p[0])
        
        resp = self.__interpret_command(packet_acc)
        client_socket.sendall(resp)

if __name__ == "__main__":
    overseer = OverSeerver(int(sys.argv[1]))
    overseer.serve_forever()
