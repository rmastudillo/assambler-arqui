from sys import argv
from collections import defaultdict
import re
from iic2343 import Basys3
import pandas as pd
import os


# Ctes.
TOKENS_COMMENTS = ['//', ';']
# TOKENS_COMMENTS = ['//']
TOKENS_STRINGS = ['"', "'"]

# Asignar las funciones si se agregan nuevos
TOKENS_BASES = ['d', 'b', 'h']
TOKEN_ARRAY_SEPARATOR = ','
TOKEN_LABEL = ':'
TOKEN_INPUTS_SEPARATOR = ','
REGISTERS = ['A', 'B']
CASOS_ESPECIALES = ('SUB B, Lit',
                    'INC A', 'INC B', 'INC (Dir)', 'INC (B)',
                    'DEC A',
                    'RET',
                    'PUSH A', 'PUSH B',
                    'POP A', 'POP B')
# Argumentos --> Archivo de entrada
input_file = str(argv[1])
# Instrucciones


def cargar_opcodes(ruta):
    """
    recibe la ruta
    retorna un diccionario con los opcodes de la primera columna del archivo
    """
    opcodes_ = defaultdict(str)
    datos = pd.read_excel(ruta, sheet_name="Etapa-2").fillna(0).reset_index()
    for index_, row in datos.iterrows():
        if index_ >= 1 and row[1] != 0:
            opcodes_[row[1]] = row[2]

    return opcodes_


my_path = os.path.abspath(os.path.dirname(__file__))
opcodes = cargar_opcodes(my_path+"/Instrucciones-computador.xlsx")


class Instruction:
    """
    Instruccion
    rom_dir
    label
    inst
    """

    def __init__(self, rom_dir, label, instr, in_1, in_2):
        self.rom_dir = rom_dir
        self.label = label
        self.inst = instr
        self.in_1 = in_1
        self.in_2 = in_2
        self.string = None

    def __str__(self):
        return (f"{self.rom_dir},{self.inst},{self.label}"
                f" {self.in_1}, {self.in_2}")


# Datos
class DataEntry:
    def __init__(self, rom_dir, label, value):
        self.rom_dir = rom_dir
        self.label = label
        self.value = value

    def __str__(self):
        return f"{self.rom_dir}, {self.label}, {self.value}, data"


# Limpiar texto
# ----- Líneas de texto -----
# Saca los comentarios
def remove_comments(text: str) -> str:
    for token in TOKENS_COMMENTS:
        text = text.split(token, 1)[0]
    return text


def trim_line(text: str) -> str:
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


def replace_multiple(text: str, *things_to_change: tuple or list) -> str:
    for nasty_stuff, nice_stuff in things_to_change:
        text = text.replace(nasty_stuff, nice_stuff)

    return text


def remove_strs(text: str, *things_i_dont_want: str) -> str:
    things_to_change = [(thing, '') for thing in things_i_dont_want]
    return replace_multiple(text, *things_to_change)


# ======= Convertir bases numericas =======
def dec2decimal(value: str = "0d") -> str:
    """
    Recibe un numero y lo retorna en decimal
    """
    if 'd' in value:  # Porque por defecto es decimal
        value = value[:-1]
    return value


def bin2decimal(value: str = "0b") -> str:
    """
    Recibe un numero y lo retorna en decimal
    """
    value = value[:-1]
    base = 2
    try:
        value = int(value, base)
    except ValueError:
        pass
    return value


def hex2decimal(value: str = "0h") -> str:
    """
    Recibe un numero y lo retorna en decimal
    """
    value = value[:-1]
    base = 16
    try:
        value = int(value, base)
    except ValueError:
        pass
    return value


# ======= Convertir letras a nros =======
def char2int(char: str = 'A') -> int:
    return ord(char)


# =======================================
def process_string(text: str) -> str:
    # Para cada token del array (', ")
    for token in TOKENS_STRINGS:
        # Reemplazar letras por números hasta que no queden letras.
        while token in text:
            super_stringy_string = text.split(token, 2)[1]
            new_string = str()

            for char in super_stringy_string:
                new_string += f"{char2int(char)}, "

            text = text.split(token, 2)[0] + \
                new_string[:-2] + text.split(token, 2)[2]

    return text


def process_arrays(text: str) -> list:
    if TOKEN_ARRAY_SEPARATOR in text:
        thingy = text.split(TOKEN_ARRAY_SEPARATOR)

    else:
        thingy = [text]

    return thingy


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


def convert_to_dataentry(entry: tuple) -> DataEntry:
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
    # line = process_bases(line)
    content[pos] = line

# Dividir data y code
temp_data = list()
data = list()
machiny_stuff = list()
type_flag = ''

for line in content:
    if line == 'DATA:':
        type_flag = 'DATA'
        continue

    elif line == 'CODE:':
        type_flag = 'CODE'
        continue

    # --------

    if type_flag == 'DATA':
        temp_data.append(line)

    elif type_flag == 'CODE':
        machiny_stuff.append(line)

    else:
        raise ValueError

# Proceso arrays
for pos, line in enumerate(temp_data):
    line = process_arrays(line)
    data += line

data = [trim_line(str(val)) for val in data]
data = assign_rom_dir(data)


for pos, line in enumerate(data):
    line = convert_to_dataentry(line)
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
                              and (line[1][0] != 'NOP' and line[1][0] != 'RET')
                              else ''),
                       instr=(line[1][0]
                              if len(line[1]) != 1
                              or (line[1][0] != 'NOP' or line[1][0] != 'RET')
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
for unused_var_in_python in data:
    if unused_var_in_python.label:
        label_pairs[
            unused_var_in_python.label] = unused_var_in_python.rom_dir
for unused_var_in_python in machiny_stuff:
    if unused_var_in_python.label:
        label_pairs[
            unused_var_in_python.label] = unused_var_in_python.rom_dir

# Borro las labels. Son innecesarias.
"""Label"""
for line in machiny_stuff:
    if line.label:
        line.label = ''
        line.inst = 'NOP'

for line in data:
    if line.label:
        line.label = ''


total_instrucciones = []
total_instrucciones_string = []

"""Comienzo a procesar las instrucciones"""

print("////////////////////////")


def convert_numbers_to_base_ten(strange_base_num: str) -> str:
    if strange_base_num[-1] == 'd':
        return dec2decimal(strange_base_num)

    elif strange_base_num[-1] == 'b':
        return bin2decimal(strange_base_num)

    elif strange_base_num[-1] == 'h':
        return hex2decimal(strange_base_num)

    else:
        raise ValueError(f"Se intentó convertir '{strange_base_num}' a "
                         f"decimal, pero no es base 2, 16 ó 10")


def procesar_indice(indice: int or str):
    # [Intr, indice, indice]
    indice = remove_strs(indice, ' ', '\t', '\n')

    if indice in REGISTERS:
        # [, 'A||B']
        return [None, indice]

    # num -> ['Lit', < var >]
    elif indice.isnumeric():
        return [indice, 'Lit']

    # label -> ['Lit', label --> lit]
    elif indice in label_pairs.keys():
        return [label_pairs[indice], 'Ins']

    elif indice[0] == '(' and indice[-1] == ')':
        t_indice = indice[1:-1]

        # 10b -> 2
        if t_indice[-1] in TOKENS_BASES:
            if t_indice in label_pairs.keys():
                return [label_pairs[t_indice], '(Dir)']

            else:
                # TODO: Debería retornar algo.
                t_indice = convert_numbers_to_base_ten(t_indice)
                return [t_indice, '(Lit)']

        if t_indice in label_pairs.keys():
            return [label_pairs[t_indice], '(Dir)']

        elif t_indice.isnumeric():
            return [t_indice, '(Dir)']

        elif t_indice in REGISTERS:
            return [None, indice]

    elif indice[-1] in TOKENS_BASES:
        """Si entra aca es porque es un numero en otra base"""
        return [convert_numbers_to_base_ten(indice), 'Lit']

    else:
        raise ValueError(f"El índice '{indice}' no está sorportado")


def generar_codigo(valor, instruccion):
    if instruccion in opcodes.keys():
        primeros16 = f'{int(valor):016b}'
        siguientes20 = (20 - len(opcodes[instruccion])) * '0' + \
                       opcodes[instruccion]
        respuesta = primeros16 + siguientes20

        return respuesta

    print(instruccion, opcodes)

    raise KeyError("OPCODE NO ENCONTRADO ERROR", instruccion)


def codigo_de_maquina(instruccion,assambler_inst):
    palabra_2 = None
    valor_2 = None

    if instruccion.inst == "NOP":
        instruccion_string = "NOP"
        resultado = (36 - len(opcodes[instruccion_string])) * '0' + \
                    opcodes[instruccion_string]

        return resultado, instruccion_string

    valor_1, palabra_1 = procesar_indice(instruccion.in_1)

    if instruccion.in_2 != '':
        valor_2, palabra_2 = procesar_indice(instruccion.in_2)

    if palabra_1 and palabra_2:

        instruccion_string = f'{assambler_inst} {palabra_1}, {palabra_2}'

        if valor_1 is not None:
            resultado = generar_codigo(valor_1, instruccion_string)

            return resultado,instruccion_string

        elif valor_2 is not None:
            resultado = generar_codigo(valor_2, instruccion_string)

            return resultado,instruccion_string

        elif palabra_1 and palabra_2:
            if instruccion_string not in opcodes.keys():
                print(opcodes)

                raise KeyError("1NO está en el opcode", instruccion_string)

            resultado = (36 - len(opcodes[instruccion_string])) * \
                        '0' + opcodes[instruccion_string]

            return resultado,instruccion_string

    elif palabra_1:
        instruccion_string = '{} {}'.format(assambler_inst,palabra_1)

        if valor_1 is not None:
            resultado = generar_codigo(valor_1, instruccion_string)

            return resultado,instruccion_string

        else:
            raise KeyError("2No está en el opcode", instruccion_string)

    else:
        raise KeyError("Instruccion no permitida", instruccion)


for key in label_pairs.keys():
    print('{} {}'.format(key, bin(int(label_pairs[key]))))

for index, d in enumerate(machiny_stuff):
    resp, assembly_inst_ = codigo_de_maquina(d, d.inst)
    print(resp[:16], ' ', resp[16:], ' ', assembly_inst_,
          '|||', d.in_1, d.in_2)
    if assembly_inst_ in CASOS_ESPECIALES:
        if assembly_inst_ == "INC (Dir)":
            push_a = (36 - len(opcodes["PUSH A"])) * '0' + opcodes["PUSH A"]
            move_a_lit = '1' + opcodes["MOV A, Lit"]
            move_a_lit = (36 - (len(move_a_lit)))*'0' + move_a_lit
            add_a_dir = (20 - len(opcodes["ADD A, (Dir)"])) * '0' + opcodes["ADD A, (Dir)"]
            add_a_dir = resp[:16] + add_a_dir
            pop_a = opcodes["POP A"].rjust(36, '0')
            pop_a_2 = '00010100000000011100'.rjust(36, '0')
            print(push_a)
            print(move_a_lit)
            print(add_a_dir)
            print(pop_a)
            print(pop_a_2)
        elif assembly_inst_ == "SUB B, Lit":
            resp_2 = opcodes["NOT B"].rjust(36, "0")
        elif assembly_inst_ == "MOV (Dir), Lit":
            direccion = f'{int(label_pairs[d.in_1[1:-1]]):016b}'
            valor = f'{int(d.in_2):016b}'
            push_a = (36 - len(opcodes["PUSH A"])) * '0' + opcodes["PUSH A"]
            move_a_lit = valor + opcodes["MOV A, Lit"].rjust(20, "0")
            move_dir_a = direccion + opcodes["MOV (Dir), A"].rjust(20, "0")
            pop_a = opcodes["POP A"].rjust(36, '0')
            pop_a_2 = '00010100000000011100'.rjust(36, '0')
        elif assembly_inst_ == "POP A":
            pop_a_2 = '00010100000000011100'.rjust(36, '0')
        elif assembly_inst_ == "POP B":
            pop_a_2 = '00010100000000011010'.rjust(36, '0')
        elif assembly_inst_ == "RET":
            ret_2 = 




# ============================================================

def convert_str_num_to_int_base_ten(as_is_data_num: str or int) -> int:
    n_val = as_is_data_num

    if str(as_is_data_num)[-1] in TOKENS_BASES:
        n_val = convert_numbers_to_base_ten(n_val)

    n_val = int(n_val)

    return n_val


def parse_data_as_move_instr(val_as_bin_literal):
    for instruction in ('MOV B, Lit', 'MOV (Dir), B'):
        instruct = f"{val_as_bin_literal} " \
                   f"{str(opcodes[instruction]).rjust(20, '0')}"

        yield instruct


def convert_data_entries_to_inst(data_entries_lst: list or tuple) -> list:
    # data -> list
    # data[0]: Asignación de datos (con labels)
    # data[0] -> DataEntry

    # DataEntry.rom_dir: int
    # DataEntry.label: int
    # DataEntry.value: int
    list_data_inst = list()

    intr_1 = 'MOV B, Lit'
    intr_2 = 'MOV (Dir), B'

    for d_entry in data:
        numeric_val = convert_str_num_to_int_base_ten(d_entry.value)
        val_as_binary = f'{int(numeric_val):016b}'
        dir_as_binary = f'{int(d_entry.rom_dir):016b}'

        list_data_inst.append(
            f"{val_as_binary}{str(opcodes[intr_1]).rjust(20, '0')}")
        list_data_inst.append(
            f"{dir_as_binary}{str(opcodes[intr_2]).rjust(20, '0')}")

    ''''''
    return list_data_inst


instrucciones_finales = [
    *convert_data_entries_to_inst(data),
    *total_instrucciones]


# for i in instrucciones_finales: print(i[:16], i[16:])
# print(" ~~~~~~~~~~~~~~~~~~~~~~~ ")
# for i in convert_data_entries_to_inst(data): print(i[:16], i[16:])
# print(" ~~~~~~~~~~~~~~~~~~~~~~~ ")
# print('~-~-~-~-SaLiDa FeA~-~-~-~-'); exit(0)  # TODO: sacar...

"""Acá se escriben las instrucciones"""


def conver_hex(binario_string):
    # print(type(hex(int(binario_string, 2))), int(
    #   hex(int(binario_string, 2))), type(int(hex(int(binario_string, 2)))))
    return int(binario_string, 2)


#rom_programmer = Basys3()
# rom_programmer.begin(port_number=1)
with open("ROM.txt", 'w') as f:

    for index, inst in enumerate(instrucciones_finales):
        f.write(inst)
        # print(inst[:16], ' ', inst[16:], ' ',
        #      instrucciones_finales_string[index])
        lista_hex = [conver_hex(inst[:4]), conver_hex(inst[4:12]),
                     conver_hex(inst[12:20]), conver_hex(inst[20:28]), conver_hex(inst[28:36])]
        lista_hex = bytearray(lista_hex)
        #rom_programmer.write(index, bytearray(lista_hex))
        f.write('\n')

# rom_programmer.end()

"""
Esto es solo para debug
"""



print("FIN")
