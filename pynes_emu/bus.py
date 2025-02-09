from pynes_emu.memory import Memory


class Bus:
    def __init__(
        self,
        cpu_memory: Memory,
        cartridge_prg_rom: Memory,
    ):
        self.cpu_memory = cpu_memory
        self.cartridge_prg_rom = cartridge_prg_rom

    def __getitem__(self, address):
        address, memory = self._access_handler(address)
        return memory[address]

    def __setitem__(self, address, value):
        address, memory = self._access_handler(address)
        memory[address] = value

    def _access_handler(self, address):
        if isinstance(address, slice):
            start, stop, step = address.start, address.stop, address.step
            mapped_start, memory = self._get_mapped_address_and_memory(start)
            mapped_stop, memory = self._get_mapped_address_and_memory(stop)
            return slice(mapped_start, mapped_stop, step), memory
        elif isinstance(address, tuple):
            address, size = address
            mapped_address, memory = self._get_mapped_address_and_memory(address)
            return (mapped_address, size), memory
        else:
            mapped_address, memory = self._get_mapped_address_and_memory(address)
            return mapped_address, memory

    def _get_mapped_address_and_memory(self, address: int) -> tuple[int, Memory]:
        # CPU memory
        if address < 0x2000:
            return (address & 0x7FF, self.cpu_memory)
        # PPU memory TBD
        elif address >= 0x2000 and address < 0x4000:
            return (address & 0x2007, None)
        # If the cartridge has 16KB of PRG ROM, the last 16KB is mirrored
        elif address >= 0x8000 and len(self.cartridge_prg_rom) == 16 * 1024:
            return (address & 0xBFFF, self.cartridge_prg_rom)
        elif address >= 0x8000:
            return (address, self.cartridge_prg_rom)
        else:
            return address, None
