from json import loads

class CPU():
    class StatusRegister():
        def __init__(self):
            self.status = [0]*8
        
        @property
        def carry(self):
            return self.status[0]   # Bit 0

        @carry.setter
        def carry(self,value):
            self.status[0] = value  # Bit 0
        
        @property
        def zero(self):
            return self.status[1]   # Bit 1

        @zero.setter
        def zero(self,value):
            self.status[1] = value  # Bit 1
        
        @property
        def intrDisable(self):
            return self.status[2]   # Bit 2

        @intrDisable.setter
        def intrDisable(self,value):
            self.status[2] = value  # Bit 2

        @property
        def decimal(self):
            return self.status[3]   # Bit 3

        @decimal.setter
        def decimal(self,value):
            self.status[3] = value  # Bit 3

        @property
        def overflow(self):
            return self.status[6]   # Bit 6

        @overflow.setter
        def overflow(self,value):
            self.status[6] = value  # Bit 6

        @property
        def negative(self):
            return self.status[7]   # Bit 7

        @negative.setter
        def negative(self,value):
            self.status[7] = value  # Bit 7

    class InstructionInfo():
        def __init__(self):
            inFile = open("./instructionInfo.json","r")
            self.info = loads(inFile.read())
            inFile.close()

    def __init__(self):
        self.ii = self.InstructionInfo()

        self.programCounter = 0
        self.flagsRegister = self.StatusRegister()
        self.accumulator = 0
        self.xIndex = 0
        self.yIndex = 0
        self.stackPointer = 0x100
        self.memory = MemoryMapper()

        self.currentInstruction = 0

    def debugCurrentInstruction(self):
        print(f"PC:{hex(self.programCounter)[2:].zfill(4)} X:{hex(self.xIndex)[2:].zfill(4)} Y:{hex(self.yIndex)[2:].zfill(4)} INSTR:{self.ii.info[str(self.currentInstruction)]['instruction']}")

    def step(self):
        self.fetchInstruction()
        self.executeInstruction()

    def fetchInstruction(self):
        self.currentInstruction = self.memory.read(self.programCounter)
        self.programCounter += 1
        self.fetchOperands()

    def fetchOperands(self):
        length = self.ii.info[str(self.currentInstruction)]["length"]
        self.operands = []
        for i in range(length):
            self.operands.append(self.memory.read(self.programCounter + i))

        self.programCounter += length
    
    def executeGetValue(self):
        if self.addressingMode == "d,x":
            value = self.memory.read((self.operands[0] + self.xIndex) % 256)
        elif self.addressingMode == "d,y":
            value = self.memory.read((self.operands[0] + self.yIndex) % 256)
        elif self.addressingMode == "a,x":
            value = self.memory.read((self.operands[1] << 2)  + self.operands[0] + self.xIndex)
        elif self.addressingMode == "a,y":
            value = self.memory.read((self.operands[1] << 2)  + self.operands[0] + self.yIndex)
        elif self.addressingMode == "(d,x)":
            value = self.memory.read(self.memory.read((self.operands[0] + self.xIndex) % 256) + self.memory.read((self.operands[0] + self.xIndex + 1) % 256) * 256)
        elif self.addressingMode == "(d),y":
            value = self.memory.read(self.memory.read(self.operands[0]) + self.memory.read((self.operands[0] + 1) % 256) * 256 + self.yIndex)
        elif self.addressingMode == "a":
            value = (self.operands[0] << 2) + self.operands[1]
        elif self.addressingMode == "r":
            value = self.programCounter + (self.operands[0]-128)
        elif self.addressingMode == "implied":
            value = 0
        elif self.addressingMode == "d":
            value = self.memory.read(self.operands[0])
        elif self.addressingMode == "(a)":
            value = self.memory.read((self.operands[1] << 2) + self.operands[0])
        elif self.addressingMode == "#":
            value = self.operands[0]
        else:
            value = None

        return value

    def executeInstruction(self):
        self.instruction = self.ii.info[str(self.currentInstruction)]["instruction"]
        self.addressingMode = self.ii.info[str(self.currentInstruction)]["addressingMode"]
        length = self.ii.info[str(self.currentInstruction)]["length"]

        value = self.executeGetValue()
        if self.instruction == "ADC":
            self.accumulator += value
            self.flagsRegister.zero = self.accumulator == 0


        if self.instruction == "LDY":
            self.yIndex = value
        elif self.instruction == "JMP":
            self.programCounter = value
        elif self.instruction == "INX":
            self.xIndex += 1
            if self.xIndex > 255: self.xIndex = 0

class MemoryMapper():
    def __init__(self):
        self.addressSpace = {}

        self.addressSpace["stack"] = {"location":0,"device":RAM(256)}
        self.addressSpace["gpram"] = {"location":256,"device":RAM(256)}
        self.addressSpace["vram"] = {"location":512,"device":RAM(256)}
        self.addressSpace["rom0"] = {"location":768,"device":ROM(2048)}

    def hexView(self,startAddress,length):
        print(f"==== 0x{hex(startAddress)[2:].zfill(4)} -> 0x{hex(startAddress+length)[2:].zfill(4)} ====")

        i = 0
        if startAddress % 8 != 0:
            while (startAddress - i) % 8 != 0:
                i += 1
        
        if i > 0:
            print(hex(startAddress-i)[2:].zfill(4)+"\t",end="")
            for j in range(i):
                print("   ",end="")

        for addr in range(startAddress,startAddress+length):
            if addr % 8 == 0:
                print()
                print(hex(addr)[2:].zfill(4), end="\t")

            print(hex(self.read(addr))[2:].zfill(2),end=" ")

        print()
        print()

    def write(self,address,value):
        for k in self.addressSpace:
            element = self.addressSpace[k]
            testAddr = element["location"]            
            size = element["device"].size

            if address >= testAddr and address < testAddr + size:
                element["device"].write(address-testAddr,value)
                return element

    def read(self,address):
        for k in self.addressSpace:
            element = self.addressSpace[k]
            testAddr = element["location"]
            size = element["device"].size

            if address >= testAddr and address < testAddr + size:
                return element["device"].content[address - testAddr]

class GeneralPurposeMemory():
    def __init__(self, size):
        self.writable = False
        self.readable = False
        self.size = size
        self.dataWidth = 8
        self.content = []
        self.maxValue = (2 ** self.dataWidth)

    def wrapMaxValue(self,value):
        return value % self.maxValue

    def write(self,address,value):
        self.content[address] = self.wrapMaxValue(value)

    def read(self,address):
        return self.content[address]

    def initZeroed(self):
        self.content = [0] * self.size

    def initMaxValue(self):
        self.content = [self.maxValue] * self.size

    def init0xEA(self):
        self.content = [0xEA] * self.size

    def initValue(self,value):
        self.content = [value] * self.size

    def initWrap(self):
        self.content = []
        for i in range(self.size):
            self.content.append(i % self.maxValue)

    def loadImage(self,file):
        data = file.read()
        for i in range(self.size):
            self.content[i] = data

class RAM(GeneralPurposeMemory):
    def __init__(self,size):
        GeneralPurposeMemory.__init__(self,size)
        self.readable = True

        self.initValue(0xEA)

class ROM(GeneralPurposeMemory):
    def __init__(self,size):
        GeneralPurposeMemory.__init__(self,size)
        self.readable = True
        self.writable = True

        self.initValue(0XEA)

if __name__ == "__main__":
    cpu = CPU()

    cpu.memory.write(0,0xE8)
    cpu.memory.write(1,0x4C)
    cpu.memory.write(2,0x00)
    cpu.memory.write(3,0x00)
    cpu.memory.hexView(0,20)
    for i in range(10):
        cpu.step()
        cpu.debugCurrentInstruction()