from pynes_emu.memory import Memory


class Bus:
    def __init__(self, memory: Memory):
        self.memory = memory

    def __getitem__(self, address):
        address = self._access_handler(address)
        return self.memory[address]

    def __setitem__(self, address, value):
        address = self._access_handler(address)
        self.memory[address] = value

    def _access_handler(self, address):
        if isinstance(address, slice):
            start, stop, step = address.start, address.stop, address.step
            start = self._mapping(start)
            stop = self._mapping(stop)
            return slice(start, stop, step)
        elif isinstance(address, tuple):
            address, size = address
            address = self._mapping(address)
            return (address, size)
        else:
            return address

    def _mapping(self, address: int) -> int:
        if address < 0x2000:
            return address & 0x1FFF
        elif address >= 0x2000 and address < 0x4000:
            return address & 0x2007
        else:
            return address
