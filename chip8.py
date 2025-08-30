import sys
from array import array
from pprint import pprint

RAM_SIZE = 4096 # 4KB
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
        self.registers = array('B',[0]*16)
        self.i = 0
        self.pc = 0x200
        self.delay_timer = 0
        self.rom = None
        self.ram = array('B',[0]*RAM_SIZE)
        # Load the font set into the first 80 bytes
        self.ram[0:len(FONT_SET)] = array('B', FONT_SET)
        self.display_buffer = [[0]*SCREEN_WIDTH]*SCREEN_HEIGHT

    def step(self):
        '''Every instruction is 16 bits, or in other words, 2 bytes or 4 nibbles, so it translates to four hexadecimal digits.'''

        first_byte = self.rom.pop(0)
        second_byte = self.rom.pop(0)

        first_nible = (first_byte >> 4)
        second_nible = (first_byte & 0b00011111)
        instruction = (first_byte << 8) | second_byte
        D1 = (instruction >> 12)
        D2 = (instruction >> 8) & 0b00001111
        D3 = (instruction >> 4) & 0b000000001111
        D4 = instruction        & 0b0000000000001111

        match(D1, D2, D3, D4):
            case (0x6, _, _, _): # 6xnn - Load normal register with immediate value
                print(f"Set register[{second_nible}] to {second_byte}")
                self.registers[second_nible] = second_byte
            case (0xA, _, _, _): # Annn - Set i to nnn
                value = (instruction & 0b0000111111111111)
                print(f"Load index register with immediate value {value}")
                self.i = value
            case (0xD, _, _, _): # Dxyn - Draw a sprite that’s n high at (v[x], v[y]); set the flag on a collision.
                print(f"draw a {D4} height sprite at v[{D2}] v[{D3}]")
                #self.draw(D4, self.registers[D2], self.registers[D3], self.i)
                #pprint(bin(self.i))
                #self.draw_screen(1, self.registers[D2], self.registers[D3], FONT_SET[0])
                #exit()
            case (0xE0, _, _, _): # Clear the screen
                self.clear_screen()
            case _:
                print("unknown instruction")
                #breakpoint()

    def clear_screen(self):
        for y in range(0, SCREEN_HEIGHT):
            for x in range(0, SCREEN_WIDTH):
                self.display_buffer[y][x] = 0

    def draw_screen(self, height: int, x: int, y: int, sprite: int):
        '''Every sprite is 8 pixels wide and can be anywhere between 1 and 15 pixels high'''

        pprint(bin(sprite))

        for yi in range(y, (y+height)):
            for xi in range(x, x+SPRITE_WIDTH):
                self.display_buffer[yi][xi] = 1

        for yi in range(0, SCREEN_HEIGHT):
            line = ''
            for xi in range(0, SCREEN_WIDTH):
                pixel = ''
                if self.display_buffer[yi][xi] == 0:
                    pixel = '.'
                else:
                    pixel = 'x'
                line = line + pixel
            print(line)

    def run(self, filename: str):
        with open(filename, mode='rb') as fp:
            rom = fp.read()
            self.rom = list(array('B', rom))
            while len(self.rom)>0:
                self.step()

filename = sys.argv[1]
vm = VM()
vm.run(filename)
