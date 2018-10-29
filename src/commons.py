from enum import Enum
from typing import List, Optional

import logging
import os
import sys

STX = 2 # type: int
ETX = 3 # type: int
NACK = int("15", 16) # type: int
RS = int("1E", 16) # type: int

class OverseerCommands(Enum):
    LOGIN = ord("A")
    LOGOUT = ord("B")
    KEEP_ALIVE = ord("C")
    REQUEST_VOTE = ord("D")
    INVALID_CMD = ord("X")
    MALFORMED_PKT = ord("Y")
    GENERAL_FAILURE = ord("Z")
    ACK = int("6", 16)

class RPCPacket(object):

    # Specifically tailored for **dictionary usage. Please don't leave them be
    # except possibly additional_info.
    def __init__(
        self,
        packet_number: int = -1,
        command: Optional[OverseerCommands] = None,
        additional_info: Optional[List[int]] = None,
        logger_name: str = "raftel-commons"
    ) -> None:
        if packet_number < 0 or command is None:
            raise ValueError("Please set the initial fields of RPCPacket properly.")
        self.packet_number = packet_number # type: int
        self.command = command # type: OverseerCommands
        self.additional_info = additional_info if additional_info else [] # type: List[int]

        self.logger = logging.getLogger(logger_name)

        if logger_name == "raftel-commons":
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)

            self.logger.addHandler(stream_handler)

        self.logger.debug("RPCPacket debug: %s %s" % (self.packet_number, type(self.packet_number)))
        self.logger.debug("RPCPacket debug: %s %s" % (self.command.value, type(self.command.value)))
        self.logger.debug("RPCPacket debug: %s %s" % (self.additional_info, type(self.additional_info)))

    def validate(self) -> bool:
        return 0 <= self.packet_number <= 256

    @staticmethod
    def validate_stream(packet_stream: List[int]) -> bool:
        return RPCPacket.parse(packet_stream).validate()

    # TODO Refactor as this is almost the same as parse method below.
    @staticmethod
    def __parse_additional_info(gathered_stream: List[int]) -> List[int]:
        i = 0
        limit = len(gathered_stream)
        additional_info = [] # type: List[int]
        byte_acc = [] # type: List[int]

        while i < limit:
            if gathered_stream[i] == RS:
                additional_info.append(int.from_bytes(bytes(byte_acc), sys.byteorder))
            else:
                byte_acc.append(gathered_stream[i])

            i += 1

        if byte_acc:
            additional_info.append(int.from_bytes(bytes(byte_acc), sys.byteorder))
        return additional_info

    @staticmethod
    def parse(packet_stream: List[int], logger_name="raftel-commons") -> "RPCPacket":
        logger = logging.getLogger(logger_name)
        logger.setLevel(int(os.environ.get("raftel_log_level", logging.INFO)))
        byte_acc = [] # type: list

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

        logger.debug("field index is %s" % field_index)
        if field_index == 2:
            packet_kwargs["additional_info"] = RPCPacket.__parse_additional_info(byte_acc)
        else:
            packet_kwargs[packet_order[field_index]] = int.from_bytes(bytes(byte_acc), sys.byteorder)

        packet_kwargs["command"] = OverseerCommands(packet_kwargs["command"])
        logger.debug("Calling RPCPacket for parsed stream")
        parsed_packet = RPCPacket(**packet_kwargs)
        return parsed_packet

    def make_sendable_stream(self) -> bytes:
        partial_packet = [
            STX, self.packet_number, RS, self.command.value
        ] # type: List[int]

        if self.additional_info:
            partial_packet.append(RS)
            partial_packet.extend(self.additional_info)
        
        partial_packet.append(ETX)

        return bytes(partial_packet)

    def __str__(self):
        return str(self.make_sendable_stream())
