from gevent.server import StreamServer
import sys

"""
The Overseer protocol is a space-delimited (byte 20) protocol which follows the
following guidelines. This is the RPC router/mechanism between raftel nodes:

- All transmissions are wrapped around STX (2) and ETX (3) bytes. Immediately
after the STX, is the packet number which is eight bits (so wrap around 256).
After that is the command.

- Commands (between STX and ETX) follow the format <command><RS><args...>
where arguments are also RS delimited. (NOTE: RS is the record separator
character, byte 1E.)

# Reserved instructions for Overseer.

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

class OverSeerver(StreamServer):

    def __init__(self, bind_port, **kwargs):
        super(OverSeerver, self).__init__(("127.0.0.1", bind_port))
        self.leader = None

    def handle(self, client_socket, address):
        print("someone connected %s" % client_socket)
        client_socket.sendall(b"hi")

if __name__ == "__main__":
    overseer = OverSeerver(int(sys.argv[1]))
    overseer.serve_forever()
