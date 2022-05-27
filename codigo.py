#!/usr/bin/python3.10

from sys import argv
from collections import defaultdict
import re

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


class Instruction:
    def __init__(self, rom_dir, label, inst, in_1, in_2):
        self.rom_dir = rom_dir
        self.label = label
        self.inst = inst
        self.in_1 = in_1
        self.in_2 = in_2

    def __str__(self):
        return f"{self.rom_dir}, {self.label}, {self.inst}, {self.in_1}, {self.in_2}"

# Datos


class DataEntry:
    def __init__(self, rom_dir, label, value):
        self.rom_dir = rom_dir
        self.label = label
        self.value = value

    def __str__(self):
        return f"{self.rom_dir}, {self.label}, {self.value}"


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

    regex_filter = "[0-9]{1,}[" + ''.join(TOKENS_BASES) + "]{1}"

    ugly_stuff = re.findall(regex_filter, text)

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


with open(input_file, 'r') as file:
    # Proceso el archivo
    # Proceso cada línea de la lista

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

"""Lloro de cansancio"""

# Separo datos en sus componentes

for pos, line in enumerate(data):
    line = convert_to_DataEntry(line)
    data[pos] = line

"""Lloro desesperadamente"""

# Proceso instrucciones
for pos, line in enumerate(machiny_stuff):
    # Demasiado cansado para usar funciones
    # A continuación les presento mi vómito de código 🤮

    # Separar labels
    if TOKEN_LABEL in line:
        line = [line]

    else:
        line = line.split(' ', 1)

        if len(line) > 1:
            line[1] = line[1].split(TOKEN_INPUTS_SEPARATOR)

            for pos_2, random_suff in enumerate(line[1]):
                line[1][pos_2] = trim_line(random_suff).replace(' ', '')
    #'rom_dir', 'label', 'inst', 'in_A', 'in_B'
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

for unused_variable_in_python in data:
    if unused_variable_in_python.label:
        label_pairs[unused_variable_in_python.label] = unused_variable_in_python.rom_dir

for unused_variable_in_python in machiny_stuff:
    if unused_variable_in_python.label:
        label_pairs[unused_variable_in_python.label] = unused_variable_in_python.rom_dir


for line in machiny_stuff:
    if line.in_1:
        # Potenciales bugs con substrings
        for key in label_pairs.keys():
            if line.in_1.replace('(', '').replace(')', '') == key:
                line.in_1 = line.in_1.replace(key, str(label_pairs[key]))

    if line.in_2:
        # Potenciales bugs con substrings
        for key in label_pairs.keys():
            if line.in_2.replace('(', '').replace(')', '') == key:
                line.in_2 = line.in_2.replace(key, str(label_pairs[key]))


# Borro las labels. Son innecesarias.
for line in machiny_stuff:
    if line.label:
        line.label = ''
        line.inst = 'NOP'

for line in data:
    if line.label:
        line.label = ''


class Literal:
    def __init__(self, lit):
        self.value = lit

    def __repr__(self):
        return "Lit"


class Direccion:
    def __init__(self, dir):
        self.value = dir

    def __repr__(self):
        return "(Dir)"


class Registro:
    def __init__(self, valor, letra):
        self.value = valor
        self.letra = letra

    def __repr__(self):
        return self.letra


class Assembler:
    def __init__(self, instruccion, representacion):
        self.instr = instruccion
        self.repr = representacion
        self.direc_j = defaultdict(int)

    def __repr__(self):
        if self.repr:
            texto = ''
            for r in self.repr:
                texto += r+"\n"
            return texto
        else:
            return "Class Assembler"


# Guardo la cosa fea en un documento por si acaso
direccion_jump = defaultdict(int)
assembler = Assembler([], [])
with open(input_file, 'r') as file:
    content = [trim_line(remove_comments(line))
               for line
               in file.readlines()
               if trim_line(remove_comments(line))]

    with open(f"{input_file}.ugly.txt", 'w') as ugly_file:
        inicial = content[:]
        for index, line in enumerate(content, start=0):
            line = line.split(" ")
            if len(line) > 1:
                line[1] = line[1].split(",")
                if len(line[1]) > 1:
                    _l = []
                    for l in line[1]:
                        if ("(" and ")") in l:
                            l = Direccion(l)
                            _l.append(l)
                            # Acá tengo que ver que hacer con las direcciones

                        elif l.isnumeric():
                            l = Literal(l)
                            _l.append(l)
                            # Acá van los literales

                        elif l.isascii():
                            if l == "A":
                                reg = Registro(None, "A")
                                _l.append(reg)
                                pass
                                #print("registro A")
                            elif l == "B":
                                reg = Registro(None, "B")
                                _l.append(reg)
                        else:
                            _l.append(l)
                    line[1] = _l
                    #print("Registro B")
                    #line[1] = _l
            else:
                if ":" in line[0]:
                    assembler.direc_j[line[0][:-1]] = index
            linea = ''
            if len(line) > 1:
                linea = linea + str(line[0]) + " "
                _l = ', '.join(map(str, line[1]))
                linea = linea+_l
            else:
                linea += str(line[0])
            assembler.repr.append(linea)
            assembler.instr.append(line)

            #ugly_file.write(str(line) + '\n')
print(assembler.direc_j)
print(assembler.instr[9][1][1].value)
print(assembler)
# ----- Para debug -----
# show_code(content)
# print()
# show_code(data)
# print()
# show_code(machiny_stuff)
