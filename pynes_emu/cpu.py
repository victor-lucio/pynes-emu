from pynes_emu.models import Addressing, ProcessorStatus, INSTRUCTION_SET
from pynes_emu.memory import Memory


# Where in Memory to find the start of the program
PC_START_INDIRECT_LOCATION = 0xFFFC


class Cpu:
    _reg_a: int = 0x00  # accumulator
    _reg_x: int = 0x00  # index register
    _reg_y: int = 0x00  # index register
    _reg_s: int = 0xFF  # stack pointer
    pc: int = 0x0000  # program counter
    reg_p: ProcessorStatus = ProcessorStatus()

    def __init__(self, memory: Memory):
        self.memory = memory
        self.reset()

    @property
    def reg_a(self):
        return self._reg_a

    @reg_a.setter
    def reg_a(self, value):
        self._reg_a = value & 0xFF

    @property
    def reg_x(self):
        return self._reg_x

    @reg_x.setter
    def reg_x(self, value):
        self._reg_x = value & 0xFF

    @property
    def reg_y(self):
        return self._reg_y

    @reg_y.setter
    def reg_y(self, value):
        self._reg_y = value & 0xFF

    @property
    def reg_s(self):
        return self._reg_s

    @reg_s.setter
    def reg_s(self, value):
        self._reg_s = value & 0xFF

    def __str__(self):
        status_flags = format(self.reg_p.to_int(), "08b")
        return f"""\
            CPU Status:
            ----------
            Accumulator (A): ${self.reg_a:04X}h (${self.reg_a:d}d)
            Index X:         ${self.reg_x:04X}h (${self.reg_x:d}d)
            Index Y:         ${self.reg_y:04X}h (${self.reg_y:d}d)
            Stack Pointer:   ${self.reg_s:04X}h (${self.reg_s:d}d)
            Program Counter: ${self.pc:04X}h (${self.pc:d}d)

            Status Flags (NV-BDIZC): {status_flags}
            N (Negative):  {self.reg_p.N}
            V (Overflow):  {self.reg_p.V}
            B (Break):     {self.reg_p.B}
            D (Decimal):   {self.reg_p.D}
            I (Interrupt): {self.reg_p.I}
            Z (Zero):      {self.reg_p.Z}
            C (Carry):     {self.reg_p.C}
        """

    def reset(self):
        # Initialize registers
        self.reg_a = 0x00  # accumulator
        self.reg_x = 0x00  # index register
        self.reg_y = 0x00  # index register
        self.reg_s = 0xFF  # stack pointer
        self.reg_p = ProcessorStatus()  # processor status

        self.pc = self.memory[PC_START_INDIRECT_LOCATION, 2]  # program counter

    def run_next(self):
        inst_name, addressing_mode, inst_data = self._fetch_next()
        self._execute(inst_name, addressing_mode, inst_data)

    def _fetch_next(self):
        op_hex = self.memory[self.pc]
        inst_name, addressing_mode, inst_size = INSTRUCTION_SET[op_hex]

        inst_data = 0
        for _ in range(inst_size - 1):
            self.pc += 1
            inst_data = inst_data << 8
            inst_data += self.memory[self.pc]

        self.pc += 1

        return inst_name, addressing_mode, inst_data

    def _push_stack(self, value):
        self.memory[0x0100 + self.reg_s] = value
        self.reg_s -= 1

    def _pop_stack(self):
        self.reg_s += 1
        return self.memory[0x0100 + self.reg_s]

    def _set_zero_and_negative(self, value):
        self.reg_p.Z = int(value == 0)
        self.reg_p.N = value >> 7

    def _execute(self, inst_name: str, addressing_mode: Addressing, inst_data: int):
        data, address = addressing_mode.get_addressing_data(
            self.memory, inst_data, self.reg_x, self.reg_y
        )

        print(f"Executing {inst_name}")
        print(f"Data: {data:04X}" if data is not None else "")
        print(f"Address: {address:04X}" if address is not None else "")

        getattr(self, f"_execute_{inst_name}")(data, address)

    def _execute_ADC(self, data, _):
        # check overflow
        a7 = self.reg_a >> 7
        d7 = data >> 7
        result = self.reg_a + data
        r7 = result >> 7
        self.reg_p.V = a7 == d7 and a7 != r7

        self.reg_p.C = result >> 8
        self.reg_a = result
        self._set_zero_and_negative(result)

    def _execute_SBC(self, data, _):
        data = ~data + 1
        self._execute_ADC(data)

    def _execute_AND(self, data, _):
        self.reg_a = self.reg_a & data
        self._set_zero_and_negative(self.reg_a)

    def _execute_EOR(self, data, _):
        self.reg_a = self.reg_a ^ data
        self._set_zero_and_negative(self.reg_a)

    def _execute_ORA(self, data, _):
        self.reg_a = self.reg_a | data
        self._set_zero_and_negative(self.reg_a)

    def _execute_ASL(self, data, address):
        if address is not None:
            result = data << 1
            self.memory[address] = result
            self.reg_p.C = data >> 7
            self._set_zero_and_negative(result)
        else:
            result = self.reg_a << 1
            self.reg_a = result
            self.reg_p.C = result >> 8
            self._set_zero_and_negative(result)

    def _execute_LSR(self, data, address):
        if address is not None:
            result = data >> 1
            self.memory[address] = result
            self.reg_p.C = data & 1
            self._set_zero_and_negative(result)
        else:
            result = self.reg_a >> 1
            self.reg_p.C = self.reg_a & 1
            self.reg_a = result
            self._set_zero_and_negative(result)

    def _execute_ROL(self, data, address):
        if address is not None:
            result = (data << 1) + self.reg_p.C
            self.memory[address] = result
            self.reg_p.C = data >> 7
            self._set_zero_and_negative(result)
        else:
            result = (self.reg_a << 1) + self.reg_p.C
            self.reg_a = result
            self.reg_p.C = result >> 8
            self._set_zero_and_negative(result)

    def _execute_ROR(self, data, address):
        if address is not None:
            result = (data >> 1) + (self.reg_p.C << 7)
            self.memory[address] = result
            self.reg_p.C = data & 1
            self._set_zero_and_negative(result)
        else:
            result = (self.reg_a >> 1) + (self.reg_p.C << 7)
            self.reg_p.C = self.reg_a & 1
            self.reg_a = result
            self._set_zero_and_negative(result)

    def _execute_BCC(self, data, _):
        if not self.reg_p.C:
            self.pc += data

    def _execute_BCS(self, data, _):
        if self.reg_p.C:
            self.pc += data

    def _execute_BNE(self, data, _):
        if not self.reg_p.Z:
            self.pc += data

    def _execute_BEQ(self, data, _):
        if self.reg_p.Z:
            self.pc += data

    def _execute_BIT(self, data, _):
        result = self.reg_a & data
        self.reg_p.V = data >> 6
        self.reg_p.N = result >> 7
        self.reg_p.Z = result == 0

    def _execute_BMI(self, data, _):
        if self.reg_p.N:
            self.pc += data

    def _execute_BPL(self, data, _):
        if not self.reg_p.N:
            self.pc += data

    def _execute_BVC(self, data, _):
        if not self.reg_p.V:
            self.pc += data

    def _execute_BVS(self, data, _):
        if self.reg_p.V:
            self.pc += data

    def _execute_CLC(self, *args):
        self.reg_p.C = 0

    def _execute_SEC(self, *args):
        self.reg_p.C = 1

    def _execute_CLD(self, *args):
        self.reg_p.D = 0

    def _execute_SED(self, *args):
        self.reg_p.D = 1

    def _execute_CLI(self, *args):
        self.reg_p.I = 0

    def _execute_SEI(self, *args):
        self.reg_p.I = 1

    def _execute_CLV(self, *args):
        self.reg_p.V = 0

    def _execute_CMP(self, data, _):
        result = self.reg_a - data
        self.reg_p.C = result >= 0
        self._set_zero_and_negative(result)

    def _execute_CPX(self, data, _):
        result = self.reg_x - data
        self.reg_p.C = result >= 0
        self._set_zero_and_negative(result)

    def _execute_CPY(self, data, _):
        result = self.reg_y - data
        self.reg_p.C = result >= 0
        self._set_zero_and_negative(result)

    def _execute_DEC(self, data, address):
        result = data - 1
        self.memory[address] = result
        self._set_zero_and_negative(result)

    def _execute_DEX(self, *args):
        self.reg_x -= 1
        self._set_zero_and_negative(self.reg_x)

    def _execute_DEY(self, *args):
        self.reg_y -= 1
        self._set_zero_and_negative(self.reg_y)

    def _execute_INC(self, data, address):
        result = data + 1
        self.memory[address] = result
        self._set_zero_and_negative(result)

    def _execute_INX(self, *args):
        self.reg_x += 1

    def _execute_INY(self, *args):
        self.reg_y += 1

    def _execute_JMP(self, data, _):
        self.pc = data

    def _execute_JSR(self, data, _):
        result = self.pc - 1
        hi_result = result >> 8
        lo_result = result & 0xFF
        self._push_stack(hi_result)
        self._push_stack(lo_result)
        self.pc = data

    def _execute_RTS(self, *args):
        result = self._pop_stack() + (self._pop_stack() << 8) + 1
        self.pc = result

    def _execute_PHA(self, *args):
        self._push_stack(self.reg_a)

    def _execute_PHP(self, *args):
        self._push_stack(self.reg_p.to_int())

    def _execute_PLA(self, *args):
        self.reg_a = self._pop_stack()
        self._set_zero_and_negative(self.reg_a)

    def _execute_PLP(self, *args):
        value = self._pop_stack()
        self.reg_p = self.reg_p.from_int(value)

    def _execute_LDA(self, data, _):
        self.reg_a = data
        self._set_zero_and_negative(self.reg_a)

    def _execute_LDX(self, data, _):
        self.reg_x = data
        self._set_zero_and_negative(self.reg_x)

    def _execute_LDY(self, data, _):
        self.reg_y = data
        self._set_zero_and_negative(self.reg_y)

    def _execute_NOP(self, *args):
        pass

    def _execute_RTI(self, *args):
        self.reg_p = self.reg_p.from_int(self._pop_stack())
        self.pc = self._pop_stack() + (self._pop_stack() << 8)

    def _execute_RTS(self, *args):
        result = self._pop_stack() + (self._pop_stack() << 8) + 1
        self.pc = result

    def _execute_STA(self, data, address):
        self.memory[address] = self.reg_a

    def _execute_STX(self, data, address):
        self.memory[address] = self.reg_x

    def _execute_STY(self, data, address):
        self.memory[address] = self.reg_y

    def _execute_TAY(self, *args):
        self.reg_y = self.reg_a
        self._set_zero_and_negative(self.reg_y)

    def _execute_TAX(self, *args):
        self.reg_x = self.reg_a
        self._set_zero_and_negative(self.reg_x)

    def _execute_TSX(self, *args):
        self.reg_x = self.reg_s
        self._set_zero_and_negative(self.reg_x)

    def _execute_TXS(self, *args):
        self.reg_s = self.reg_x

    def _execute_TXA(self, *args):
        self.reg_a = self.reg_x
        self._set_zero_and_negative(self.reg_a)

    def _execute_TYA(self, *args):
        self.reg_a = self.reg_y
        self._set_zero_and_negative(self.reg_a)

    def _execute_BRK(self, *args):
        result = self.pc + 1
        hi_result = result >> 8
        lo_result = result & 0xFF
        self._push_stack(hi_result)
        self._push_stack(lo_result)
        self._push_stack(self.reg_p.to_int())
        self.reg_p.B = 1
