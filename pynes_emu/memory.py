class Memory(list):
    def __init__(self, size: int = 0xFFFF, base_address: int = 0x0000):
        super().__init__([0x00] * size)
        self.base_address = base_address

    def __getitem__(self, key):
        if isinstance(key, tuple):
            address, size = key
            if size != 2:
                raise ValueError(
                    "Memory can only be read in chunks of size 2 (16-bit reads)"
                )

            # Adjust the address by subtracting base_address
            adjusted_address = address - self.base_address
            lo_value = super().__getitem__(adjusted_address)
            hi_value = super().__getitem__(adjusted_address + 1)

            # Combine bytes in little-endian order
            return ((hi_value << 8) + lo_value) & 0xFFFF

        elif isinstance(key, slice):
            # Adjust slice boundaries by subtracting base_address
            start = key.start - self.base_address if key.start is not None else 0
            stop = key.stop - self.base_address if key.stop is not None else None
            new_key = slice(start, stop, key.step)
            return super().__getitem__(new_key)

        else:
            # For an integer index, subtract the base_address
            return super().__getitem__(key - self.base_address)

    def __setitem__(self, key, value):
        if isinstance(key, tuple):
            address, size = key
            if size != 2:
                raise ValueError(
                    "Memory can only be read in chunks of size 2 (16-bit reads)"
                )

            # Adjust the address by subtracting base_address
            adjusted_address = address - self.base_address

            # Split the value into two bytes (little-endian)
            value_lo = value & 0xFF
            value_hi = (value >> 8) & 0xFF

            # Write the bytes at the adjusted addresses
            super().__setitem__(adjusted_address, value_lo)
            super().__setitem__(adjusted_address + 1, value_hi)

        elif isinstance(key, slice):
            # Adjust the slice boundaries by subtracting base_address
            start = key.start - self.base_address if key.start is not None else 0
            stop = key.stop - self.base_address if key.stop is not None else None
            new_key = slice(start, stop, key.step)

            if isinstance(value, list):
                # Mask each value to 8-bit
                masked_values = [single_value & 0xFF for single_value in value]
                super().__setitem__(new_key, masked_values)
            else:
                raise TypeError("Slice assignment requires a list of integer values")

        else:
            # For an integer key, subtract the base_address
            super().__setitem__(key - self.base_address, value & 0xFF)

    def __repr__(self):
        output = []
        for i, value in enumerate(self):
            # Display the effective absolute address (index + base_address)
            output.append(f"${i + self.base_address:04X}h: ${value:02X}h ({value:d}d)")
        return "\n".join(output)
