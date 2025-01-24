class Memory:
    def __init__(self, size: int = 0x2_000):
        self._memory = [0x00] * size

    def __getitem__(self, key):
        if isinstance(key, tuple):
            address, size = key
            if size != 2:
                raise ValueError(
                    "Memory can only be read in chunks of size 2 (16-bit reads)"
                )

            # Read the two bytes in little-endian order
            lo_value = self._memory[address]
            hi_value = self._memory[address + 1]

            # Convert to little-endian
            value = (hi_value << 8) + lo_value

            # Ensure the address is within the valid range
            return value & 0xFFFF
        else:
            # Single byte read (8-bit)
            return self._memory[key]

    def __setitem__(self, key: int, value: int):
        if isinstance(key, tuple):
            address, size = key
            if size != 2:
                raise ValueError(
                    "Memory can only be read in chunks of size 2 (16-bit reads)"
                )

            value_lo = value & 0xFF
            value_hi = (value >> 8) & 0xFF

            # last byte first
            self._memory[address] = value_lo
            # then first byte
            self._memory[address + 1] = value_hi
        elif isinstance(key, slice) and isinstance(value, list):
            masked_values = [single_value & 0xFF for single_value in value]
            self._memory[key] = masked_values
        else:
            self._memory[key] = value & 0xFF
