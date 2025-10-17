import sys
import traceback
import time
from array import array
from pprint import pprint

RAM_SIZE = 4096
SCREEN_WIDTH = 64
SCREEN_HEIGHT = 32
SPRITE_WIDTH = 8
BYTE_LENGHT = 8
SPEED = 0

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
        self.stack = []
        self.display_buffer = [[0 for i in range(SCREEN_WIDTH)] for j in range(SCREEN_HEIGHT)]

    def step(self):
        '''Every instruction is 16 bits, or in other words, 2 bytes or 4 nibbles, so it translates to four hexadecimal digits.'''

        try:
            first_byte = self.ram[self.pc]
            second_byte = self.ram[self.pc+1]
            self.pc += 2

            instruction = (first_byte << BYTE_LENGHT) | second_byte

            N1 = self.extract_bits_from_byte(first_byte, 0,4)  # (first_byte >> 4)
            N2 = self.extract_bits_from_byte(first_byte, 4,4)  # (first_byte & 0b00001111)
            N3 = self.extract_bits_from_byte(second_byte, 0,4)
            N4 = self.extract_bits_from_byte(second_byte, 4,4)


            match(N1, N2, N3, N4):
                case (0x0, 0x0, 0xE, 0x0):
                    print(f"clear the screen")
                    self.clear_screen()
                case (0x1, _, _, _):
                    value = instruction & 0b0000111111111111
                    print(f"jump to {value}")
                    self.pc = value
                case (0x2, _, _, _):
                    value = instruction & 0b0000111111111111
                    print(f"call the subroutine at {value}")
                    self.stack.append(self.pc)
                    self.pc = value
                case (0x3, _, _, _):
                    print(f"skip the next instruction if {self.v[N2]} = {second_byte}")
                    if self.v[N2] == second_byte:
                        self.pc += 2
                case (0x4, _, _, _):
                    print(f"skip the next instruction if {self.v[N2]} != {second_byte}")
                    if self.v[N2] != second_byte:
                        self.pc += 2
                case (0x5, _, _, 0x0):
                    print(f"skip the next instruction if {self.v[N2]} = {self.v[N3]}")
                    if self.v[N2] == self.v[N3]:
                        self.pc += 2
                case (0x6, _, _, _):
                    print(f"set register[{N2}] to {second_byte}")
                    self.v[N2] = second_byte
                case (0x7, _, _, _):
                    print(f"add {self.v[N2]}, {second_byte}")
                    self.v[N2] = (self.v[N2] + second_byte) % 256
                case (0x8, _, _, 0x0):
                    print(f"set {self.v[N2]} to {self.v[N3]}")
                    self.v[N2] = self.v[N3]
                case (0x8, _, _, 0x1):
                    print(f"set {self.v[N2]} to OR {self.v[N2]}, {self.v[N3]}")
                    self.v[N2] = self.v[N3] | self.v[N3]
                case (0x8, _, _, 0x2):
                    print(f"set {self.v[N2]} to AND {self.v[N2]}, {self.v[N3]}")
                    self.v[N2] = self.v[N3] & self.v[N3]
                case (0x8, _, _, 0x3):
                    print(f"set {self.v[N2]} to XOR {self.v[N2]}, {self.v[N3]}")
                    self.v[N2] = self.v[N3] ^ self.v[N3]
                case (0x8, _, _, 0x4):
                    print(f"set {self.v[N2]} to ADD {self.v[N2]}, {self.v[N3]} with carry flag")
                    res = self.v[N3] + self.v[N3]
                    if res < 256:
                        self.v[N2] = res
                        self.v[0xF] = 0
                    else:
                        self.v[N2] = res % 256
                        self.v[0xF] = 1
                case (0x9, _, _, 0x0):
                    print(f"skip the next instruction if {self.v[N2]} does not equal {self.v[N3]}")
                    if self.v[N2] != self.v[N3]:
                        self.pc += 2
                case (0xA, _, _, _):
                    value = (instruction & 0b0000111111111111)
                    print(f"set index register with immediate value {value}")
                    self.i = value
                case (0xD, _, _, _):
                    print(f"draw a {N4} height sprite at (v[{N2}]={self.v[N2]}, v[{N3}]={self.v[N3]})")
                    self.draw_sprite(self.v[N2], self.v[N3], N4)
                case (0x0, _, 0xE, 0xE):
                    print(f"return from a subroutine")
                    self.pc = self.stack.pop()
                case _:
                    print(f"instruction {hex(instruction)} not implemented yet!")
                    breakpoint()
            time.sleep(SPEED)

        except Exception as e:
            print(f"exception '{e}' at pc = {self.pc}, instruction = {hex(instruction)}")
            breakpoint()


    def clear_screen(self):
        for y in range(0, SCREEN_HEIGHT):
            for x in range(0, SCREEN_WIDTH):
                self.display_buffer[y][x] = 0

    def extract_bits_from_byte(self, data: int, start: int, length: int) -> int:
        bitmask = 0
        for i in range(0, length):
            bitmask = (bitmask << 1) | 1

        shift = BYTE_LENGHT-start-length
        bits = (data >> shift) & bitmask
        return bits

    def draw_sprite(self, x: int, y: int, height: int):
        '''Dxyn - DRW Vx, Vy, nibble
Display n-byte sprite starting at memory location I at (Vx, Vy), set VF = collision (TODO).

The interpreter reads n bytes from memory, starting at the address stored in I. These bytes are then displayed as sprites on screen at coordinates (Vx, Vy). Sprites are XORed onto the existing screen'''

        # Every sprite is 8 pixels wide and can be anywhere between 1 and 15 pixels high
        for yi in range(0, height):
            row = self.ram[self.i + yi]
            for xi in range(0, SPRITE_WIDTH):

                if xi+x-1 >= SCREEN_WIDTH or yi+y-1 >= SCREEN_HEIGHT:
                    print(f"trying to draw outside screen ({yi+y-1},{xi+x-1}), skipping instruction")
                    continue

                new_bit = self.extract_bits_from_byte(row, xi, 1)
                current_bit = self.display_buffer[yi+y-1][xi+x-1]
                self.display_buffer[yi+y-1][xi+x-1] = new_bit ^ current_bit

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
        # Load program to memory starting at address 0x200 (512)
        self.ram[0x200:len(self.rom)] = array('B', rom)

        while True:
            self.step()


filename = sys.argv[1]
vm = VM()
vm.run(filename)
