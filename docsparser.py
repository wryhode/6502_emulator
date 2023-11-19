import csv
from json import dumps
data = list(csv.reader(open("./convertcsv.csv")))

oneOp = [
    "#",
    "d,x",
    "d,y",
    "d",
    "(d,x)",
    "(d),y",
    "r"
]
twoOp = [
    "a",
    "a,x",
    "a,y",
    "(a)"
]

def decodeAM(am):
    am = am.lower()
    if am in oneOp:
        return 1
    elif am in twoOp:
        return 2
    else:
        return 0
    
    raise ValueError

i = 0
table = {}
for y in data:
    for x in y:
        if x != "":
            addressingMode = x.split(" ")
            if len(addressingMode) > 1:
                am = addressingMode[1]
            else:
                am = "implied"
            
            length = decodeAM(am)

            table[i] = {"instruction":addressingMode[0], "addressingMode":am.lower(), "length":length}
    
        i += 1

file = open("./instructionInfo.json","w")
file.write(dumps(table,indent = 4))
file.close()