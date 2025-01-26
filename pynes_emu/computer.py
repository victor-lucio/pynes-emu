from pynes_emu.cpu import Cpu, PC_START_INDIRECT_LOCATION
from pynes_emu.memory import Memory


class Computer:
    def __init__(self, program):
        self.memory = Memory()
        self._copy_program_to_memory(program)

        self.cpu = Cpu(memory=self.memory)
        self.cpu.reset()
        print(self.cpu)

    def _copy_program_to_memory(self, program):

        # read program from programs folder
        if isinstance(program, str):
            with open(f"programs/{program}", "r") as f:
                program_raw = list(f.readlines())

        # remove comments, empty spaces and empty lines
        program_str = [line.strip() for line in program_raw if line and not line.startswith("//")]

        # convert hex strings to integers
        program_hex = [int(line, 16) for line in program_str]

        # set the program counter to the start of the program
        start_address = 0x8000
        self.memory[PC_START_INDIRECT_LOCATION, 2] = start_address

        # load program
        self.memory[start_address : start_address + len(program_hex)] = program_hex
        return

    def run(self):
        self.cpu.run_next()
        print(self.cpu)
