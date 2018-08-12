import logging
import os
import sys

STX = 2
ETX = 3
ACK = int("6", 16)
NACK = int("15", 16)
RS = int("1E", 16)

class RPCPacket(object):

    # Specifically tailored for **dictionary usage. Please don't leave them be
    # except possible additional_info.
    def __init__(
        self, packet_number: int =None, command: int =None, additional_info=None,
        logger_name="raftel-commons"
    ) -> None:
        self.packet_number = packet_number
        self.command = command
        self.additional_info = additional_info if additional_info else []

        self.logger = logging.getLogger(logger_name)

        if logger_name == "raftel-commons":
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)

            self.logger.addHandler(stream_handler)

        self.logger.debug("RPCPacket debug: %s %s" % (self.packet_number, type(self.packet_number)))
        self.logger.debug("RPCPacket debug: %s %s" % (self.command, type(self.command)))
        self.logger.debug("RPCPacket debug: %s %s" % (self.additional_info, type(self.additional_info)))

    @staticmethod
    def parse(packet_stream, logger_name="raftel-common"):
        logger = logging.getLogger(logger_name)
        byte_acc = []

        packet_order = ("packet_number", "command", "additional_info")
        packet_kwargs = {"logger_name": logger_name}
        field_index = 0

        # Automagically ignore STX and ETX
        i = 1
        limit = len(packet_stream) - 1

        while i < limit:
            logger.debug("inspecting: %s" % packet_stream[i])
            if packet_stream[i] == RS and field_index < 2:
                packet_kwargs[packet_order[field_index]] = int.from_bytes(bytes(byte_acc), sys.byteorder)
                byte_acc = []
                field_index += 1
            else:
                byte_acc.append(packet_stream[i])
            i += 1

        packet_kwargs[packet_order[field_index]] = int.from_bytes(bytes(byte_acc), sys.byteorder)
        logger.info("Calling RPCPacket for parsed stream")
        parsed_packet = RPCPacket(**packet_kwargs)
        return parsed_packet

    def make_sendable_stream(self):
        addtl_info_encoded = [ord(c) for c in self.additional_info]
        partial_packet = [
            STX, self.packet_number, RS, self.command
        ]

        if addtl_info_encoded:
            partial_packet.append(RS)
            partial_packet.extend(addtl_info_encoded)
        
        partial_packet.append(ETX)

        return bytes(partial_packet)

    def __str__(self):
        return str(self.make_sendable_stream())
