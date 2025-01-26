class Memory(list):
    def __init__(self, size: int = 0xFFFF):
        super().__init__([0x00] * size)

    def __getitem__(self, key):
        if isinstance(key, tuple):
            address, size = key
            if size != 2:
                raise ValueError(
                    "Memory can only be read in chunks of size 2 (16-bit reads)"
                )

            # Read the two bytes in little-endian order
            lo_value = super().__getitem__(address)
            hi_value = super().__getitem__(address + 1)

            # Convert to little-endian
            value = (hi_value << 8) + lo_value

            # Ensure the address is within the valid range
            return value & 0xFFFF
        else:
            # Single byte read (8-bit)
            return super().__getitem__(key)

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
            super().__setitem__(address, value_lo)
            # then first byte
            super().__setitem__(address + 1, value_hi)
        elif isinstance(key, slice) and isinstance(value, list):
            masked_values = [single_value & 0xFF for single_value in value]
            super().__setitem__(key, masked_values)
        else:
            super().__setitem__(key, value & 0xFF)

    def __repr__(self):
        output = []
        for i, value in enumerate(self):
            if i > 0x2000:
                break
            elif value != 0:
                output.append(f"${i:04X}h: ${value:02X}h ({value:d}d)")
        return "\n".join(output)
