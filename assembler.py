from sys import argv
from collections import defaultdict
import re
import csv
from iic2343 import Basys3


# Ctes.
TOKENS_COMMENTS = ['//', ';']
TOKENS_STRINGS = ['"', "'"]
# Asignar las funciones si se agregan nuevos
TOKENS_BASES = ['d', 'b', 'h']
TOKEN_ARRAY_SEPARATOR = ','
TOKEN_LABEL = ':'
TOKEN_INPUTS_SEPARATOR = ','
REGISTERS = ['A', 'B']

# Argumentos --> Archivo de entrada
input_file = str(argv[1])
# Instrucciones


def cargar_opcodes(ruta):
    opcodes = defaultdict(str)
    with open(ruta, mode='r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=';')
        line_count = 0
        for row in csv_reader:
            if line_count == 0 or line_count == 1:
                line_count += 1
                continue
            else:
                line_count += 1
                opcodes[row[0]] = row[1]
    return opcodes


opcodes = cargar_opcodes("Instrucciones-computador.csv")


class Instruction:
    def __init__(self, rom_dir, label, inst, in_1, in_2):
        self.rom_dir = rom_dir
        self.label = label
        self.inst = inst
        self.in_1 = in_1
        self.in_2 = in_2
        self.string = None

    def __str__(self):
        return f"{self.rom_dir},{self.inst},{self.label} {self.in_1}, {self.in_2}"

# Datos


class DataEntry:
    def __init__(self, rom_dir, label, value):
        self.rom_dir = rom_dir
        self.label = label
        self.value = value

    def __str__(self):
        return f"{self.rom_dir}, {self.label}, {self.value}, data"


# ----- Líneas de texto -----
# Saca los comentarios
def remove_comments(text: str) -> str:
    for token in TOKENS_COMMENTS:
        text = text.split(token, 1)[0]
    return text

# Saco bordes


def trim_line(text: str) -> str:
    # Porque mágicamente es feliz si lo corro 2 veces
    for _ in range(2):
        # Sacamos lo saltos de línea
        # Sacamos los tabs del extremo
        # Sacamos los espacios de los extremos
        for thingy in ("\n", "\t", ' '):
            text = text.strip(thingy)

    return text

# Saco dobles espacios y \t


def clear_mid_spaces(text: str) -> str:
    text = text.replace("\t", ' ')

    double_space = '  '

    while double_space in text:
        text = text.replace(double_space, ' ')

    return text

# ----- Convertir bases numericas -----


def dec2decimal(value: str = "0d") -> str:
    if 'd' in value:  # Porque por defecto es decimal
        value = value[:-1]

    return value


def bin2decimal(value: str = "0b") -> str:
    value = value[:-1]
    base = 2

    try:
        value = int(value, base)

    except ValueError:
        pass

    return value


def hex2decimal(value: str = "0h") -> str:
    print("estoy aqui")
    # TODO: Problema del yo del futuro
    value = value[:-1]
    base = 16

    try:
        value = int(value, base)

    except ValueError:
        pass

    return value


def process_bases(text: str) -> str:

    # BUG: Variables que incluyen
    regex_filter = "\s--[0-9a-fA-F]+[--]?\s"

    ugly_stuff = re.findall(regex_filter, text)
    print(ugly_stuff, text)
    while ugly_stuff:

        ugly_stuff = str(ugly_stuff[0])

        match ugly_stuff[-1]:
            case 'd':
                nice_stuff = dec2decimal(ugly_stuff)

            case 'b':
                nice_stuff = bin2decimal(ugly_stuff)

            case 'h':
                nice_stuff = hex2decimal(ugly_stuff)

            case _:
                raise ValueError

        parts = text.split(ugly_stuff)
        text = parts[0] + str(nice_stuff)
        text += parts[1] if len(parts) > 1 else ''

        ugly_stuff = re.findall(regex_filter, text)

    return text

# ----- Cosas de strings -----
# Caracteres ascii a nros.


def char2int(char: str = 'A') -> int:
    return ord(char)

# Convierto todos los acaracteres a numerso
# Es treméndamente ineficiente.
# Tal vez después la arregle


def process_string(text: str) -> str:
    # Para cada token del array (', ")
    for token in TOKENS_STRINGS:
        # Reemplazar letras por números hasta que no queden letras.
        while token in text:
            string = text.split(token, 2)[1]
            new_string = str()

            for char in string:
                new_string += f"{char2int(char)}, "

            text = text.split(token, 2)[0] + \
                new_string[:-2] + text.split(token, 2)[2]

    return text


# ----- Cosas de arrays -----
def process_arrays(text: str) -> list:
    if TOKEN_ARRAY_SEPARATOR in text:
        thingy = text.split(TOKEN_ARRAY_SEPARATOR)

    else:
        thingy = [text]

    return thingy

# ----- Para debug -----


def show_code(code: list) -> None:
    for code_line in code:
        print(code_line)

# ----- Direcciones de memoria y cosas feas realcionadas -----
# Asigna direcciones de memoria a las instrucciones
# instr -> (dir, instr)


def assign_rom_dir(code: list, starting_dir: int = 0) -> list:
    instruction_counter = starting_dir
    organized_code = list()

    for instr in code:
        organized_code.append((instruction_counter,
                               instr))

        instruction_counter += 1

    return organized_code


def convert_to_DataEntry(entry: tuple) -> DataEntry:
    if len(entry[1].split(' ')) > 1:
        data_label = entry[1].split(' ')[0]
        data_value = entry[1].split(' ')[1]

    else:
        data_label = ''
        data_value = entry[1].split(' ')[0]

    entry = DataEntry(rom_dir=entry[0],
                      label=data_label,
                      value=data_value)

    return entry

# ----- Cosas mágicas con tokens -----


def split_token(text: str) -> list:
    return list()


''' Comienzo a leer el archivo y procesar las instrucciones '''

with open(input_file, 'r', encoding='utf-8') as file:
    # Proceso el archivo
    # Proceso cada línea de la lista
    print(file)
    content = [trim_line(remove_comments(line))
               for line
               in file.readlines()
               if trim_line(remove_comments(line))]

for pos, line in enumerate(content):
    line = process_string(line)
    line = clear_mid_spaces(line)
    line = process_bases(line)
    content[pos] = line

# Dividir data y code
temp_data, data, machiny_stuff = list(), list(), list()
type_flag = ''

for line in content:
    if line == 'DATA:':
        type_flag = 'DATA'
        continue

    elif line == 'CODE:':
        type_flag = 'CODE'
        continue

    # --------

    match type_flag:
        case 'DATA':
            temp_data.append(line)

        case 'CODE':
            machiny_stuff.append(line)

        case _:
            raise ValueError

# Proceso arrays
for pos, line in enumerate(temp_data):
    line = process_arrays(line)
    data += line

data = [trim_line(str(val)) for val in data]
data = assign_rom_dir(data)


for pos, line in enumerate(data):
    line = convert_to_DataEntry(line)
    data[pos] = line

# Proceso instrucciones
for pos, line in enumerate(machiny_stuff):
    # Demasiado cansado para usar funciones
    # Separar labels
    if TOKEN_LABEL in line:
        line = [line]
    else:
        line = line.split(' ', 1)
        if len(line) > 1:
            line[1] = line[1].split(TOKEN_INPUTS_SEPARATOR)
            for pos_2, random_suff in enumerate(line[1]):
                line[1][pos_2] = trim_line(random_suff).replace(' ', '')
    # 'rom_dir', 'label', 'inst', 'in_A', 'in_B'
    machiny_stuff[pos] = line

machiny_stuff = assign_rom_dir(machiny_stuff, len(data))

for pos, line in enumerate(machiny_stuff):
    # Hace magia, no pregunten.
    line = Instruction(rom_dir=line[0],
                       label=(line[1][0][:-1]
                              if len(line[1]) == 1
                              and line[1][0] != 'NOP'
                              else ''),
                       inst=(line[1][0]
                             if len(line[1]) != 1
                             or line[1][0] == 'NOP'
                             else ''),
                       in_1=(line[1][1][0]
                             if len(line[1]) != 1
                             else ''),
                       in_2=(line[1][1][1])
                       if len(line[1]) != 1
                       and len(line[1][1]) != 1
                       else '')
    machiny_stuff[pos] = line


label_pairs = dict()
"""
Acá se hace un diccionario con los labels para el acceso
"""
for unused_variable_in_python in data:
    if unused_variable_in_python.label:
        label_pairs[
            unused_variable_in_python.label] = unused_variable_in_python.rom_dir
for unused_variable_in_python in machiny_stuff:
    if unused_variable_in_python.label:
        label_pairs[
            unused_variable_in_python.label] = unused_variable_in_python.rom_dir

# for line in machiny_stuff:
#    if line.in_1:
#        # Potenciales bugs con substrings
#        for key in label_pairs.keys():
#            if line.in_1.replace('(', '').replace(')', '') == key:
#                line.in_1 = line.in_1.replace(key, str(label_pairs[key]))
#
#    if line.in_2:
#        # Potenciales bugs con substrings
#        for key in label_pairs.keys():
#            if line.in_2.replace('(', '').replace(')', '') == key:
#                line.in_2 = line.in_2.replace(key, str(label_pairs[key]))

"""
"""
# Borro las labels. Son innecesarias.
for line in machiny_stuff:
    if line.label:
        line.label = ''
        line.inst = 'NOP'

for line in data:
    if line.label:
        line.label = ''

total_instrucciones = []
total_instrucciones_string = []

for d in machiny_stuff:
    _dir_1 = (d.in_1.replace('(', '').replace(')', '')
              in label_pairs.keys())
    _dir_1_num = (d.in_1.replace('(', '').replace(')',
                  '').replace(' ', '').isdigit())

    _dir_2 = (d.in_2.replace('(', '').replace(')', '')
              in label_pairs.keys())
    _dir_2_num = (d.in_2.replace('(', '').replace(')',
                  '').replace(' ', '').isdigit())
    _reg_1 = (("A" in d.in_1) or ("B" in d.in_1))
    _reg_2 = (("A" in d.in_2) or ("B" in d.in_2))
    _lit_1 = d.in_1.isdigit()
    _lit_2 = d.in_2.isdigit()
    lit_dir = ""
    direccion = 0
    if d.inst == "NOP":
        d.string = "NOP"
        direccion = int(0)

    elif _reg_1 and _reg_2:
        d.string = "{} {}, {}".format(d.inst, d.in_1, d.in_2)
        direccion = int(0)

    elif _reg_1 and _lit_2:
        d.string = "{} {}, {}".format(d.inst, d.in_1, "Lit")
        direccion = int(d.in_2)

    elif _reg_1 and (_dir_2 or _dir_2_num):
        d.string = "{} {}, {}".format(d.inst, d.in_1, "(Dir)")
        direccion = d.in_2.replace('(', '').replace(')', '')
        if _dir_2_num:
            direccion = int(d.in_2.replace('(', '').replace(')',
                                                            '').replace(' ', ''))
        else:
            direccion = label_pairs[direccion]

    elif (_dir_1 or _dir_1_num) and _reg_2:
        d.string = "{} {}, {}".format(d.inst, "(Dir)", d.in_2)
        direccion = d.in_1.replace('(', '').replace(')', '')
        if _dir_1_num:
            direccion = int(d.in_1.replace('(', '').replace(')',
                                                            '').replace(' ', ''))
        else:
            direccion = label_pairs[direccion]
    elif (_dir_1 or _dir_1_num) and not d.in_2:
        if "(" in d.in_1:
            d.string = "{} {}".format(d.inst, "(Dir)")
            direccion = d.in_1.replace('(', '').replace(')', '')
            if _dir_1_num:
                direccion = int(d.in_1.replace('(', '').replace(')',
                                                                '').replace(' ', ''))
            else:
                direccion = label_pairs[direccion]

        else:
            d.string = "{} {}".format(d.inst, "Ins")
            direccion = d.in_1.replace('(', '').replace(')', '')
            direccion = label_pairs[direccion]
    elif _reg_1 and not d.in_2:
        d.string = "{} {}".format(d.inst, d.in_1)
        direccion = int(0)
    lit_dir = f'{int(direccion):016b}'
    if d.string in opcodes.keys():
        instrucciones = lit_dir + \
            (20-len(opcodes[d.string]))*'0'+opcodes[d.string]
        total_instrucciones.append(instrucciones)

    else:
        print("OPCODE NO ENCONTRADO ERROR", d)
    total_instrucciones_string.append(d.string)

list_data_inst = []
list_data_str = []
for d in data:
    # Primera op
    string = "MOV B, Lit".format(d.value)
    try:
        valor_literal = int(d.value)
    except:
        match d.value[-1]:
            case 'd':
                valor_literal = dec2decimal(d.value[-1])

            case 'b':
                valor_literal = bin2decimal(d.value[-1])

            case 'h':
                valor_literal = hex2decimal(d.value[-1])

            case _:
                raise ValueError

    list_data_str.append(string)
    lit_dir = f'{int(valor_literal):016b}'
    if string in opcodes.keys():
        instrucciones = lit_dir + \
            (20-len(opcodes[string]))*'0'+opcodes[string]
        list_data_inst.append(instrucciones)
    else:
        print("OPCODE NO ENCONTRADO ERROR", d)
    # Segunda op
    string = "MOV (Dir), B"
    list_data_str.append(string)
    direccion = d.rom_dir

    lit_dir = f'{int(direccion):016b}'
    if string in opcodes.keys():
        instrucciones = lit_dir + \
            (20-len(opcodes[string]))*'0'+opcodes[string]
        list_data_inst.append(instrucciones)
    else:
        print("OPCODE NO ENCONTRADO ERROR", d)
instrucciones_finales = [*list_data_inst, *total_instrucciones]
instrucciones_finales_string = [*list_data_str, *total_instrucciones_string]
"""
Acá se escriben las instrucciones
"""


def conver_hex(binario_string):
    # print(type(hex(int(binario_string, 2))), int(
    #   hex(int(binario_string, 2))), type(int(hex(int(binario_string, 2)))))
    return int(binario_string, 2)


rom_programmer = Basys3()
rom_programmer.begin(port_number=1)
with open("ROM.txt", 'w') as f:

    for index, inst in enumerate(instrucciones_finales):
        f.write(inst)
        print(inst[:16], ' ', inst[16:])
        lista_hex = [conver_hex(inst[:4]), conver_hex(inst[4:12]),
                     conver_hex(inst[12:20]), conver_hex(inst[20:28]), conver_hex(inst[28:36])]
        lista_hex = bytearray(lista_hex)
        rom_programmer.write(index, bytearray(lista_hex))
        f.write('\n')

rom_programmer.end()

"""
Esto es solo para debug
"""

with open("ROM_instruccion.txt", 'w') as f:
    for inst in instrucciones_finales_string:
        f.write(inst)
        f.write('\n')
print("FIN")
