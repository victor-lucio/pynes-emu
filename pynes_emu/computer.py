from pynes_emu.cpu import Cpu, PC_START_INDIRECT_LOCATION
from pynes_emu.memory import Memory


class Computer:
    def __init__(self):
        self.memory = Memory(0xFFFF)
        self._copy_program_to_memory()

        self.cpu = Cpu(memory=self.memory)
        self.cpu.reset()
        print(self.cpu)

    def _copy_program_to_memory(self):
        # set the program counter to the start of the program
        self.memory[PC_START_INDIRECT_LOCATION, 2] = 0x00FF

        program = [0xA9, 0xC0, 0xAA, 0xE8]

        # load program
        self.memory[0x00FF : 0x00FF + len(program)] = program
        return

    def run(self):
        self.cpu.run_next()
        print(self.cpu)
