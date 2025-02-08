import pygame
import time
import random
import sys
from pynes_emu.cpu import Cpu, PC_START_INDIRECT_LOCATION
from pynes_emu.memory import Memory
from pynes_emu.bus import Bus
from pynes_emu.cartridge_reader import CartridgeReader

SCREEN_SCALE = 20  # Scale up pixels for visibility
GRID_SIZE = 32
SCREEN_SIZE = GRID_SIZE * SCREEN_SCALE


class Computer:
    def __init__(self, rom_path, start_address=0x8000):
        self.start_address = start_address
        self.cpu_memory = Memory(size=2 * 1024)
        cartridge_reader = CartridgeReader(rom_path)
        self.prg_rom = self._get_rom_from_cartridge(cartridge_reader)
        
        self.bus = Bus(cpu_memory=self.cpu_memory, cartridge_prg_rom=self.prg_rom)
        self.bus[PC_START_INDIRECT_LOCATION, 2] = self.start_address

        # init pygame
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
        self.screen.fill((0, 0, 0))

        self.cpu = Cpu(bus=self.bus)
        self.cpu.reset()

    def _get_rom_from_cartridge(self, cartridge_reader: CartridgeReader):
        prg_rom = Memory(size=cartridge_reader.prg_rom_size, base_address=0x8000)
        prg_rom[:] = cartridge_reader.read_prg_rom()
        return prg_rom

    def _get_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.KEYDOWN:
                return pygame.key.name(event.key)

    def _draw_screen(self):
        # Iterate through the 32x32 grid
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # Calculate memory address for this pixel (0x0200 + y*32 + x)
                mem_addr = 0x0200 + (y * GRID_SIZE) + x
                color_value = self.memory[mem_addr]

                # Convert memory value to RGB color (example mapping)
                # You can modify this mapping based on your needs
                if color_value == 0:
                    color = pygame.Color("black")  # Black
                elif color_value == 1:
                    color = pygame.Color("white")  # White
                elif color_value in [2, 9]:
                    color = pygame.Color("grey")  # Red
                elif color_value in [3, 10]:
                    color = pygame.Color("red")  # Red
                elif color_value in [4, 11]:
                    color = pygame.Color("green")  # Green
                elif color_value in [5, 12]:
                    color = pygame.Color("blue")  # Green
                elif color_value in [6, 13]:
                    color = pygame.Color("magenta")  # Green
                elif color_value in [7, 14]:
                    color = pygame.Color("yellow")  # Green
                else:
                    color = pygame.Color("cyan")  # White for other values

                # Draw scaled pixel
                pygame.draw.rect(
                    self.screen,
                    color,
                    (x * SCREEN_SCALE, y * SCREEN_SCALE, SCREEN_SCALE, SCREEN_SCALE),
                )

        pygame.display.flip()  # Update the display

    def run(self):
        if self.cpu.pc < self.start_address + len(self.program_hex):
            self.cpu.run_next()
            print(self.cpu)

    def run_game(self):
        while self.cpu.pc < self.start_address + len(self.program_hex):
            input = self._get_input()
            if input == "down":
                self.memory[0x00FF] = 0x73
            elif input == "up":
                self.memory[0x00FF] = 0x77
            elif input == "left":
                self.memory[0x00FF] = 0x61
            elif input == "right":
                self.memory[0x00FF] = 0x64
            elif input == "quit":
                sys.exit()

            self.memory[0x00FE] = random.randint(1, 16)

            self.cpu.run_next()

            # Only redraw if screen memory has changed
            screen_memory = self.memory[0x0200 : 0x0200 + GRID_SIZE * GRID_SIZE]
            if not hasattr(self, "_last_screen") or screen_memory != self._last_screen:
                self._draw_screen()
                self._last_screen = screen_memory.copy()

            time.sleep(0.00025)
