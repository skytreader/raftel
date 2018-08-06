from gevent.server import StreamServer
import sys

"""
The Overseer protocol is a space-delimited (byte 32) protocol which follows the
following guidelines:

- All transmissions are wrapped around STX (2) and ETX (3) bytes. Immediately
after the STX, is the packet number which is a eight bits (so wrap around 256).
- Commands (between STX and ETX) follow the format <command><space><args...>
where arguments are also space delimited. arguments are prohibited from having
spaces in them.

# Reserved instructions for Overseer.

- Every command will be ACKed (6) or NACKed (21), depending on whether the
transaction is successful or not. NACKs will give the following reasons:
    
    Z - General failure
    Y - Malformed packet, please retransmit.
    X - Invalid/unknown command.

Responses will also start with the packet number they are acknowledging.
- When a client connects to the Overseer, it connects with a log-in command (A).
- Graceful termination would happen by sendind a log-out command (B).
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
