from enum import Enum
from functools import partial
from dataclasses import dataclass
from pynes_emu.utils import address_to_big_endian

@dataclass
class ProcessorStatus:
    N: int = 0  # Negative
    V: int = 0  # Overflow
    _: int = 0  # Unused
    B: int = 0  # Break
    D: int = 0  # Decimal
    I: int = 0  # Interrupt
    Z: int = 0  # Zero
    C: int = 0  # Carry

    def to_int(self) -> int:
        """Convert flags to an 8-bit integer in NV-BDIZC order"""
        return (
            self.N << 7
            | self.V << 6
            | self._ << 5
            | self.B << 4
            | self.D << 3
            | self.I << 2
            | self.Z << 1
            | self.C
        )

    @classmethod
    def from_int(cls, value: int) -> "ProcessorStatus":
        """Create ProcessorStatus from an 8-bit integer"""
        value = value & 0xFF
        return cls(
            N=(value >> 7) & 1,
            V=(value >> 6) & 1,
            _=(value >> 5) & 1,
            B=(value >> 4) & 1,
            D=(value >> 3) & 1,
            I=(value >> 2) & 1,
            Z=(value >> 1) & 1,
            C=value & 1,
        )


class Addressing(Enum):
    """
    Addressing modes for the 6502 CPU.

    Each addressing mode is a partial function that takes:
        data: The instruction operand data
        memory: The system memory
        reg_x: The X register value
        reg_y: The Y register value

    Returns a tuple of:
        - The data value to operate on
        - The effective address (or None if not a memory operation)
    """

    def _direct_value(data, *_):
        return (data, None)

    def _no_value(*_):
        return (None, None)

    def _direct_access_zp(data, memory, *_):
        return (memory[data], data)

    def _direct_access_abs(data, memory, *_):
        data_be = address_to_big_endian(data)
        return (memory[data_be], data_be)

    def _shifted_access_x_zp(data, memory, reg_x, _):
        return (memory[(data + reg_x) & 0xFF], (data + reg_x) & 0xFF)

    def _shifted_access_y_zp(data, memory, _, reg_y):
        return (memory[(data + reg_y) & 0xFF], (data + reg_y) & 0xFF)

    def _shifted_access_x_abs(data, memory, reg_x, _):
        data_be = address_to_big_endian(data)
        return (memory[data_be + reg_x], data_be + reg_x)

    def _shifted_access_y_abs(data, memory, _, reg_y):
        data_be = address_to_big_endian(data)
        return (memory[data_be + reg_y], data_be + reg_y)

    def _indirect_access(data, memory, *_):
        data_be = address_to_big_endian(data)
        return (memory[memory[data_be]], memory[data_be])

    def _indexed_indirect_access(data, memory, reg_x, _):
        address_lo = memory[data + reg_x]
        address_hi = memory[data + reg_x + 1]
        address = (address_hi << 8) + address_lo
        data = memory[address]
        return (data, address)

    def _indirect_indexed_access(data, memory, _, reg_y):
        address_lo = memory[data] + reg_y
        address_hi = memory[data + 1]
        address = (address_hi << 8) + address_lo
        data = memory[address]
        return (data, address)

    # No memory access Addressing
    IMMEDIATE = partial(_direct_value)
    RELATIVE = partial(_direct_value)
    ACCUMULATOR = partial(_no_value)
    IMPLIED = partial(_no_value)
    # Memory access Addressing
    ZERO_PAGE = partial(_direct_access_zp)
    ZERO_PAGE_X = partial(_shifted_access_x_zp)
    ZERO_PAGE_Y = partial(_shifted_access_y_zp)
    ABSOLUTE = partial(_direct_access_abs)
    ABSOLUTE_X = partial(_shifted_access_x_abs)
    ABSOLUTE_Y = partial(_shifted_access_y_abs)
    INDIRECT = partial(_indirect_access)
    INDIRECT_X = partial(_indexed_indirect_access)
    INDIRECT_Y = partial(_indirect_indexed_access)

    def get_addressing_data(self, memory, data, reg_x, reg_y) -> tuple[int, int]:
        return self.value(data, memory, reg_x, reg_y)


INSTRUCTION_SET = {
    # opcode: (instruction_name, addressing_mode, size_in_bytes)
    # Load/Store Operations
    # Load/Store Operations
    # LDA - Load Accumulator
    0xA9: ("LDA", Addressing.IMMEDIATE, 2),  # Load Accumulator with immediate
    0xA5: ("LDA", Addressing.ZERO_PAGE, 2),  # Load Accumulator from zero page
    0xB5: ("LDA", Addressing.ZERO_PAGE_X, 2),  # Load Accumulator from zero page,X
    0xAD: ("LDA", Addressing.ABSOLUTE, 3),  # Load Accumulator from absolute
    0xBD: ("LDA", Addressing.ABSOLUTE_X, 3),  # Load Accumulator from absolute,X
    0xB9: ("LDA", Addressing.ABSOLUTE_Y, 3),  # Load Accumulator from absolute,Y
    0xA1: ("LDA", Addressing.INDIRECT_X, 2),  # Load Accumulator from (indirect,X)
    0xB1: ("LDA", Addressing.INDIRECT_Y, 2),  # Load Accumulator from (indirect),Y
    # LDX - Load X Register
    0xA2: ("LDX", Addressing.IMMEDIATE, 2),  # Load X Register with immediate
    0xA6: ("LDX", Addressing.ZERO_PAGE, 2),  # Load X Register from zero page
    0xB6: ("LDX", Addressing.ZERO_PAGE_Y, 2),  # Load X Register from zero page,Y
    0xAE: ("LDX", Addressing.ABSOLUTE, 3),  # Load X Register from absolute
    0xBE: ("LDX", Addressing.ABSOLUTE_Y, 3),  # Load X Register from absolute,Y
    # LDY - Load Y Register
    0xA0: ("LDY", Addressing.IMMEDIATE, 2),  # Load Y Register with immediate
    0xA4: ("LDY", Addressing.ZERO_PAGE, 2),  # Load Y Register from zero page
    0xB4: ("LDY", Addressing.ZERO_PAGE_X, 2),  # Load Y Register from zero page,X
    0xAC: ("LDY", Addressing.ABSOLUTE, 3),  # Load Y Register from absolute
    0xBC: ("LDY", Addressing.ABSOLUTE_X, 3),  # Load Y Register from absolute,X
    # STA - Store Accumulator
    0x85: ("STA", Addressing.ZERO_PAGE, 2),  # Store Accumulator in zero page
    0x95: ("STA", Addressing.ZERO_PAGE_X, 2),  # Store Accumulator in zero page,X
    0x8D: ("STA", Addressing.ABSOLUTE, 3),  # Store Accumulator in absolute
    0x9D: ("STA", Addressing.ABSOLUTE_X, 3),  # Store Accumulator in absolute,X
    0x99: ("STA", Addressing.ABSOLUTE_Y, 3),  # Store Accumulator in absolute,Y
    0x81: ("STA", Addressing.INDIRECT_X, 2),  # Store Accumulator in (indirect,X)
    0x91: ("STA", Addressing.INDIRECT_Y, 2),  # Store Accumulator in (indirect),Y
    # STX - Store X Register
    0x86: ("STX", Addressing.ZERO_PAGE, 2),  # Store X Register
    0x96: ("STX", Addressing.ZERO_PAGE_Y, 2),  # Store X Register
    0x8E: ("STX", Addressing.ABSOLUTE, 3),  # Store X Register
    # STY - Store Y Register
    0x84: ("STY", Addressing.ZERO_PAGE, 2),  # Store Y Register
    0x94: ("STY", Addressing.ZERO_PAGE_X, 2),  # Store Y Register
    0x8C: ("STY", Addressing.ABSOLUTE, 3),  # Store Y Register
    # Register Transfers
    0xAA: ("TAX", Addressing.IMPLIED, 1),  # Transfer Accumulator to X
    0x8A: ("TXA", Addressing.IMPLIED, 1),  # Transfer X to Accumulator
    0xA8: ("TAY", Addressing.IMPLIED, 1),  # Transfer Accumulator to Y
    0x98: ("TYA", Addressing.IMPLIED, 1),  # Transfer Y to Accumulator
    0xBA: ("TSX", Addressing.IMPLIED, 1),  # Transfer Stack Pointer to X
    0x9A: ("TXS", Addressing.IMPLIED, 1),  # Transfer X to Stack Pointer
    # Stack Operations
    0x48: ("PHA", Addressing.IMPLIED, 1),  # Push Accumulator
    0x68: ("PLA", Addressing.IMPLIED, 1),  # Pull Accumulator
    0x08: ("PHP", Addressing.IMPLIED, 1),  # Push Processor Status
    0x28: ("PLP", Addressing.IMPLIED, 1),  # Pull Processor Status
    # Logical Operations
    # AND
    0x29: ("AND", Addressing.IMMEDIATE, 2),  # AND with immediate
    0x25: ("AND", Addressing.ZERO_PAGE, 2),  # AND with zero page
    0x35: ("AND", Addressing.ZERO_PAGE_X, 2),  # AND with zero page,X
    0x2D: ("AND", Addressing.ABSOLUTE, 3),  # AND with absolute
    0x3D: ("AND", Addressing.ABSOLUTE_X, 3),  # AND with absolute,X
    0x39: ("AND", Addressing.ABSOLUTE_Y, 3),  # AND with absolute,Y
    0x21: ("AND", Addressing.INDIRECT_X, 2),  # AND with (indirect,X)
    0x31: ("AND", Addressing.INDIRECT_Y, 2),  # AND with (indirect),Y
    # EOR - Exclusive OR
    0x49: ("EOR", Addressing.IMMEDIATE, 2),  # Exclusive OR with immediate
    0x45: ("EOR", Addressing.ZERO_PAGE, 2),  # Exclusive OR with zero page
    0x55: ("EOR", Addressing.ZERO_PAGE_X, 2),  # Exclusive OR with zero page,X
    0x4D: ("EOR", Addressing.ABSOLUTE, 3),  # Exclusive OR with absolute
    0x5D: ("EOR", Addressing.ABSOLUTE_X, 3),  # Exclusive OR with absolute,X
    0x59: ("EOR", Addressing.ABSOLUTE_Y, 3),  # Exclusive OR with absolute,Y
    0x41: ("EOR", Addressing.INDIRECT_X, 2),  # Exclusive OR with (indirect,X)
    0x51: ("EOR", Addressing.INDIRECT_Y, 2),  # Exclusive OR with (indirect),Y
    # ORA - OR
    0x09: ("ORA", Addressing.IMMEDIATE, 2),  # OR with immediate
    0x05: ("ORA", Addressing.ZERO_PAGE, 2),  # OR with zero page
    0x15: ("ORA", Addressing.ZERO_PAGE_X, 2),  # OR with zero page,X
    0x0D: ("ORA", Addressing.ABSOLUTE, 3),  # OR with absolute
    0x1D: ("ORA", Addressing.ABSOLUTE_X, 3),  # OR with absolute,X
    0x19: ("ORA", Addressing.ABSOLUTE_Y, 3),  # OR with absolute,Y
    0x01: ("ORA", Addressing.INDIRECT_X, 2),  # OR with (indirect,X)
    0x11: ("ORA", Addressing.INDIRECT_Y, 2),  # OR with (indirect),Y
    # Shift Operations
    # ASL - Arithmetic Shift Left
    0x0A: ("ASL", Addressing.ACCUMULATOR, 1),  # Arithmetic Shift Left Accumulator
    0x06: ("ASL", Addressing.ZERO_PAGE, 2),  # Arithmetic Shift Left zero page
    0x16: ("ASL", Addressing.ZERO_PAGE_X, 2),  # Arithmetic Shift Left zero page,X
    0x0E: ("ASL", Addressing.ABSOLUTE, 3),  # Arithmetic Shift Left absolute
    0x1E: ("ASL", Addressing.ABSOLUTE_X, 3),  # Arithmetic Shift Left absolute,X
    # LSR - Logical Shift Right
    0x4A: ("LSR", Addressing.ACCUMULATOR, 1),  # Logical Shift Right Accumulator
    0x46: ("LSR", Addressing.ZERO_PAGE, 2),  # Logical Shift Right zero page
    0x56: ("LSR", Addressing.ZERO_PAGE_X, 2),  # Logical Shift Right zero page,X
    0x4E: ("LSR", Addressing.ABSOLUTE, 3),  # Logical Shift Right absolute
    0x5E: ("LSR", Addressing.ABSOLUTE_X, 3),  # Logical Shift Right absolute,X
    # ROL - Rotate Left
    0x2A: ("ROL", Addressing.ACCUMULATOR, 1),  # Rotate Left Accumulator
    0x26: ("ROL", Addressing.ZERO_PAGE, 2),  # Rotate Left zero page
    0x36: ("ROL", Addressing.ZERO_PAGE_X, 2),  # Rotate Left zero page,X
    0x2E: ("ROL", Addressing.ABSOLUTE, 3),  # Rotate Left absolute
    0x3E: ("ROL", Addressing.ABSOLUTE_X, 3),  # Rotate Left absolute,X
    # ROR - Rotate Right
    0x6A: ("ROR", Addressing.ACCUMULATOR, 1),  # Rotate Right Accumulator
    0x66: ("ROR", Addressing.ZERO_PAGE, 2),  # Rotate Right zero page
    0x76: ("ROR", Addressing.ZERO_PAGE_X, 2),  # Rotate Right zero page,X
    0x6E: ("ROR", Addressing.ABSOLUTE, 3),  # Rotate Right absolute
    0x7E: ("ROR", Addressing.ABSOLUTE_X, 3),  # Rotate Right absolute,X
    # Arithmetic Operations
    # ADC - Add with Carry
    0x69: ("ADC", Addressing.IMMEDIATE, 2),  # Add with Carry immediate
    0x65: ("ADC", Addressing.ZERO_PAGE, 2),  # Add with Carry zero page
    0x75: ("ADC", Addressing.ZERO_PAGE_X, 2),  # Add with Carry zero page,X
    0x6D: ("ADC", Addressing.ABSOLUTE, 3),  # Add with Carry absolute
    0x7D: ("ADC", Addressing.ABSOLUTE_X, 3),  # Add with Carry absolute,X
    0x79: ("ADC", Addressing.ABSOLUTE_Y, 3),  # Add with Carry absolute,Y
    0x61: ("ADC", Addressing.INDIRECT_X, 2),  # Add with Carry (indirect,X)
    0x71: ("ADC", Addressing.INDIRECT_Y, 2),  # Add with Carry (indirect),Y
    # SBC - Subtract with Carry
    0xE9: ("SBC", Addressing.IMMEDIATE, 2),  # Subtract with Carry immediate
    0xE5: ("SBC", Addressing.ZERO_PAGE, 2),  # Subtract with Carry zero page
    0xF5: ("SBC", Addressing.ZERO_PAGE_X, 2),  # Subtract with Carry zero page,X
    0xED: ("SBC", Addressing.ABSOLUTE, 3),  # Subtract with Carry absolute
    0xFD: ("SBC", Addressing.ABSOLUTE_X, 3),  # Subtract with Carry absolute,X
    0xF9: ("SBC", Addressing.ABSOLUTE_Y, 3),  # Subtract with Carry absolute,Y
    0xE1: ("SBC", Addressing.INDIRECT_X, 2),  # Subtract with Carry (indirect,X)
    0xF1: ("SBC", Addressing.INDIRECT_Y, 2),  # Subtract with Carry (indirect),Y
    # Increments & Decrements
    # Register Operations
    0xE8: ("INX", Addressing.IMPLIED, 1),  # Increment X Register
    0xC8: ("INY", Addressing.IMPLIED, 1),  # Increment Y Register
    0xCA: ("DEX", Addressing.IMPLIED, 1),  # Decrement X Register
    0x88: ("DEY", Addressing.IMPLIED, 1),  # Decrement Y Register
    # Memory Operations
    # INC - Increment Memory
    0xE6: ("INC", Addressing.ZERO_PAGE, 2),  # Increment Memory
    0xF6: ("INC", Addressing.ZERO_PAGE_X, 2),  # Increment Memory
    0xEE: ("INC", Addressing.ABSOLUTE, 3),  # Increment Memory
    0xFE: ("INC", Addressing.ABSOLUTE_X, 3),  # Increment Memory
    # DEC - Decrement Memory
    0xC6: ("DEC", Addressing.ZERO_PAGE, 2),  # Decrement Memory
    0xD6: ("DEC", Addressing.ZERO_PAGE_X, 2),  # Decrement Memory
    0xCE: ("DEC", Addressing.ABSOLUTE, 3),  # Decrement Memory
    0xDE: ("DEC", Addressing.ABSOLUTE_X, 3),  # Decrement Memory
    # Compare Operations
    # CMP - Compare Accumulator
    0xC9: ("CMP", Addressing.IMMEDIATE, 2),  # Compare Accumulator
    0xC5: ("CMP", Addressing.ZERO_PAGE, 2),  # Compare Accumulator
    0xD5: ("CMP", Addressing.ZERO_PAGE_X, 2),  # Compare Accumulator
    0xCD: ("CMP", Addressing.ABSOLUTE, 3),  # Compare Accumulator
    0xDD: ("CMP", Addressing.ABSOLUTE_X, 3),  # Compare Accumulator
    0xD9: ("CMP", Addressing.ABSOLUTE_Y, 3),  # Compare Accumulator
    0xC1: ("CMP", Addressing.INDIRECT_X, 2),  # Compare Accumulator
    0xD1: ("CMP", Addressing.INDIRECT_Y, 2),  # Compare Accumulator
    # CPX - Compare X Register
    0xE0: ("CPX", Addressing.IMMEDIATE, 2),  # Compare X Register
    0xE4: ("CPX", Addressing.ZERO_PAGE, 2),  # Compare X Register
    0xEC: ("CPX", Addressing.ABSOLUTE, 3),  # Compare X Register
    # CPY - Compare Y Register
    0xC0: ("CPY", Addressing.IMMEDIATE, 2),  # Compare Y Register
    0xC4: ("CPY", Addressing.ZERO_PAGE, 2),  # Compare Y Register
    0xCC: ("CPY", Addressing.ABSOLUTE, 3),  # Compare Y Register
    # Branches
    0x90: ("BCC", Addressing.RELATIVE, 2),  # Branch if Carry Clear
    0xB0: ("BCS", Addressing.RELATIVE, 2),  # Branch if Carry Set
    0xF0: ("BEQ", Addressing.RELATIVE, 2),  # Branch if Equal
    0x30: ("BMI", Addressing.RELATIVE, 2),  # Branch if Minus
    0xD0: ("BNE", Addressing.RELATIVE, 2),  # Branch if Not Equal
    0x10: ("BPL", Addressing.RELATIVE, 2),  # Branch if Positive
    0x50: ("BVC", Addressing.RELATIVE, 2),  # Branch if Overflow Clear
    0x70: ("BVS", Addressing.RELATIVE, 2),  # Branch if Overflow Set
    # Status Flag Changes
    0x18: ("CLC", Addressing.IMPLIED, 1),  # Clear Carry Flag
    0x38: ("SEC", Addressing.IMPLIED, 1),  # Set Carry Flag
    0x58: ("CLI", Addressing.IMPLIED, 1),  # Clear Interrupt Disable
    0x78: ("SEI", Addressing.IMPLIED, 1),  # Set Interrupt Disable
    0xB8: ("CLV", Addressing.IMPLIED, 1),  # Clear Overflow Flag
    0xD8: ("CLD", Addressing.IMPLIED, 1),  # Clear Decimal Mode
    0xF8: ("SED", Addressing.IMPLIED, 1),  # Set Decimal Mode
    # System Functions
    0x00: ("BRK", Addressing.IMPLIED, 1),  # Force Interrupt
    0x40: ("RTI", Addressing.IMPLIED, 1),  # Return from Interrupt
    0x60: ("RTS", Addressing.IMPLIED, 1),  # Return from Subroutine
    0x20: ("JSR", Addressing.ABSOLUTE, 3),  # Jump to Subroutine
    0x4C: ("JMP", Addressing.ABSOLUTE, 3),  # Jump
    0x6C: ("JMP", Addressing.INDIRECT, 3),  # Jump Indirect
    0x24: ("BIT", Addressing.ZERO_PAGE, 2),  # Test Bits in Memory with Accumulator
    0x2C: ("BIT", Addressing.ABSOLUTE, 3),  # Test Bits in Memory with Accumulator
    0xEA: ("NOP", Addressing.IMPLIED, 1),  # No Operation
}
