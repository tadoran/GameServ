from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Iterable


@dataclass
class ProtocolCommand:
    abbr: str
    receive_callback: Callable # Action when message is recieved
    send_callback: Callable

    def __hash__(self):
        return hash(self.abbr)

    def encode_command(self, data):
        return f"{self.abbr}:{data}"


class Protocol:
    _commands = {}

    def __init__(self):
        pass

    def add_command(self, command: ProtocolCommand):
        self._commands.update({(command.abbr, command)})

    def __getitem__(self, key: str) -> ProtocolCommand:
        item = self._commands.get(key, None)
        if not item:
            item = self.missing_command(key)
        return item

    def missing_command(self, key, *args, **kwargs):
        raise AttributeError(f"Command {key} is not registered in {self.__class__.__name__}")

    def get_message_handler(self, msg: str) -> tuple[Callable, Iterable]:
        try:
            command, args = msg.split(sep=":", maxsplit=1)
            protocol_command = self._commands[command]
            return protocol_command.abbr, protocol_command.receive_callback, args
        except ValueError as e:
            print("Message is malformed, ignoring it")
            return self.missing_command, ()

