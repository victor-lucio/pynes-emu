from pynes_emu.utils import MirroringType

PRG_ROM_PAGE_SIZE = 16 * 1024
CHR_ROM_PAGE_SIZE = 8 * 1024


class CartridgeReader:
    prg_rom_size: int
    chr_rom_size: int
    prg_rom_start: int
    chr_rom_start: int
    mapper_type: int
    mirroring_type: MirroringType

    def __init__(self, file_path):
        self.file_path = file_path
        with open(self.file_path, "rb") as f:
            self._parse_header(f.read(16))

    def read_prg_rom(self):
        with open(self.file_path, "rb") as f:
            f.seek(self.prg_rom_start)
            return f.read(self.prg_rom_size)

    def read_chr_rom(self):
        with open(self.file_path, "rb") as f:
            f.seek(self.chr_rom_start)
            return f.read(self.chr_rom_size)

    def _parse_header(self, header: bytes):
        control_byte_1 = header[6]
        control_byte_2 = header[7]

        if header[:4] != b"NES\x1a":
            raise ValueError("Invalid NES header")

        if (control_byte_2 & 0x0C) == 0x08:
            raise ValueError("NES 2.0 format not supported")

        self.prg_rom_size = header[4] * PRG_ROM_PAGE_SIZE
        self.chr_rom_size = header[5] * CHR_ROM_PAGE_SIZE

        skip_trainer = control_byte_1 & 0x04

        self.prg_rom_start = 16 + (skip_trainer * 512)
        self.chr_rom_start = self.prg_rom_start + self.prg_rom_size

        self.mapper_type = (control_byte_1 & 0xF0) | (control_byte_2 >> 4)

        mirroring_type_value = control_byte_1 & 0x03
        if mirroring_type_value == 0:
            self.mirroring_type = MirroringType.HORIZONTAL
        elif mirroring_type_value == 1:
            self.mirroring_type = MirroringType.VERTICAL
        elif mirroring_type_value >= 2:
            self.mirroring_type = MirroringType.FOUR_SCREEN
