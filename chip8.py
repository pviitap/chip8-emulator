import sys
import time
from array import array
from pprint import pprint

RAM_SIZE = 4096
SCREEN_WIDTH = 64
SCREEN_HEIGHT = 32
SPRITE_WIDTH = 8

# Each character in the font set is an 8 × 5 sprite
FONT_SET = [
0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
0x20, 0x60, 0x20, 0x20, 0x70, # 1
0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
0x90, 0x90, 0xF0, 0x10, 0x10, # 4
0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
0xF0, 0x10, 0x20, 0x40, 0x40, # 7
0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
0xF0, 0x90, 0xF0, 0x90, 0x90, # A
0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
0xF0, 0x80, 0x80, 0x80, 0xF0, # C
0xE0, 0x90, 0x90, 0x90, 0xE0, # D
0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
0xF0, 0x80, 0xF0, 0x80, 0x80  # F
]

class VM:
    def __init__(self):
        self.v = array('B',[0]*16)
        self.i = 0
        self.pc = 0x200
        self.delay_timer = 0
        self.rom = None
        self.ram = array('B',[0]*RAM_SIZE)
        # Load the font set into the first 80 bytes
        self.ram[0:len(FONT_SET)] = array('B', FONT_SET)
        self.display_buffer = [[0 for i in range(SCREEN_WIDTH)] for j in range(SCREEN_HEIGHT)]

    def step(self):
        '''Every instruction is 16 bits, or in other words, 2 bytes or 4 nibbles, so it translates to four hexadecimal digits.'''

        first_byte = self.ram[self.pc]
        second_byte = self.ram[self.pc+1]
        self.pc += 2

        #first_nible = (first_byte >> 4)
        #second_nible = (first_byte & 0b00001111)

        instruction = (first_byte << 8) | second_byte

        D1 = self.extract_bits_from_byte(first_byte, 0,4)
        D2 = self.extract_bits_from_byte(first_byte, 4,4)
        D3 = self.extract_bits_from_byte(second_byte, 0,4)
        D4 = self.extract_bits_from_byte(second_byte, 4,4)

        match(D1, D2, D3, D4):
            case (0x6, _, _, _): # 6xnn - Load normal register with immediate value
                print(f"Set register[{D2}] to {second_byte}")
                self.v[D2] = second_byte
            case (0xA, _, _, _): # Annn - Set i to nnn
                value = (instruction & 0b0000111111111111)
                print(f"Load index register with immediate value {value}")
                self.i = value
            case (0xD, _, _, _): # Dxyn - Draw a sprite that’s n high at (v[x], v[y]); set the flag on a collision.
                print(f"draw a {D4} height sprite at v[{D2}]={self.v[D2]} v[{D3}]={self.v[D3]}")
                self.draw_screen(self.v[D2], self.v[D3], D4)
            case (0x0, 0x0, 0xE, 0x0): # 00e0 - Clear the screen
                self.clear_screen()
            case (0x1, _, _, _): # 1nnn - Jump to nnn
                value = (instruction & 0b0000111111111111)
                print(f"Jump to {value}")
                self.pc = value
            case _:
                print("unknown instruction " + hex(instruction))
                breakpoint()
        time.sleep(0.1)


    def clear_screen(self):
        for y in range(0, SCREEN_HEIGHT):
            for x in range(0, SCREEN_WIDTH):
                self.display_buffer[y][x] = 0

    def extract_bits_from_byte(self, data: int, start: int, length: int) -> int:
        byte_len = 8

        bitmask = 0
        for i in range(0, length):
            bitmask = (bitmask << 1) | 1

        shift = byte_len-start-length
        bits = (data >> shift) & bitmask
        return bits

    def draw_screen(self, x: int, y: int, height: int):

        # Every sprite is 8 pixels wide and can be anywhere between 1 and 15 pixels high
        for yi in range(0, height):
            row = (self.ram[self.i + yi])
            for xi in range(0, SPRITE_WIDTH):
                bit = self.extract_bits_from_byte(row, xi, 1)
                self.display_buffer[yi+y][xi+x] = bit ^ self.display_buffer[yi+y][xi+x]

        for yi in range(0, SCREEN_HEIGHT):
            line = ''
            for xi in range(0, SCREEN_WIDTH):
                if self.display_buffer[yi][xi] == 0:
                    char = ' '
                else:
                    char = 'x'
                line = line + char
            print(line)

    def run(self, filename: str):
        with open(filename, mode='rb') as fp:
            rom = fp.read()
            self.rom = list(array('B', rom))
            # Load program to memory starting at address 0x200
            self.ram[512:len(self.rom)] = array('B', rom)

        while True:
            self.step()

filename = sys.argv[1]
vm = VM()
vm.run(filename)
