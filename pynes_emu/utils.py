def address_to_big_endian(data):
    data_lo = data & 0xFF
    data_hi = (data >> 8) & 0xFF
    return (data_lo << 8) + data_hi


def signed_8_bit_to_int(data):
    if data >> 7:
        return data - 256
    return data
