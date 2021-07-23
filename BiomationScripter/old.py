# import EchoProto as EP
# import FelixProto as FP
# import OTProto as OP
import os

class PlateLayout:
    def __init__(self, Name, Type):
        self.name = Name
        self.type = Type
        self.rows = None
        self.columns = None
        self.content = {}

    def define_format(self, rows, columns):
        self.rows = rows
        self.columns = columns

    def add_content(self, Well, Reagent, Volume, Liquid_Class = False):
        # Volume should always be uL
        if Liquid_Class == False:
            Liquid_Class = "Unknown"
        if ":" in Well:
            for w in well_range(Well):
                self.add_content(w, Reagent, Volume, Liquid_Class)
        elif Well in self.content:
            self.content[Well].append([Reagent,float(Volume), Liquid_Class])
        else:
            self.content[Well] = [ [Reagent,float(Volume), Liquid_Class] ]

    def get_content(self, Well):
        return(self.content[Well])

    def get_content(self):
        return(self.content)

    def print(self):
        print("Information for " + self.name)
        print("Plate Type: " + self.type)
        content = self.get_content()
        print("Well\tVolume(uL)\tLiquid Class\tReagent")
        for well in content:
            for c in content[well]:
                print(well+"\t"+str(c[1])+"\t\t"+c[2]+"\t\t"+c[0])

    def clear_content(self):
        self.content = {}

def Lrange(L1,L2): # Between L1 and L2 INCLUSIVE of L1 and L2
    L1 = ord(L1.upper())
    L2 = ord(L2.upper())
    for L in range(L1,L2+1):
        yield(chr(L))

def well_range(Well):
    first, last = Well.split(":")
    firstL = first[0]
    lastL = last[0]
    firstN = int(first[1:len(first)])
    lastN = int(last[1:len(last)])
    rows = []
    cols = []
    wells = []
    for L in Lrange(firstL,lastL):
        for N in range(firstN,lastN+1):
            wells.append(L+str(N))
    return(wells)
