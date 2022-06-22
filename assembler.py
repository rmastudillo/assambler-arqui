from sys import argv
from collections import defaultdict
from iic2343 import Basys3
import pandas as pd
import os


# Ctes.
TOKENS_COMMENTS = ('//', ';')
# TOKENS_COMMENTS = ('//', )
TOKENS_STRINGS = ('"', "'")

# Asignar las funciones si se agregan nuevos
TOKENS_BASES = ('d', 'b', 'h')
TOKEN_ARRAY_SEPARATOR = ','
TOKEN_LABEL = ':'
TOKEN_INPUTS_SEPARATOR = ','
REGISTERS = ('A', 'B')
CASOS_ESPECIALES = ('SUB B, Lit','SHR (B), A',"ADD A, Ins","ADD B, Ins","OR A, Ins","OR B, Ins","MOV (A), Ins","MOV (B), Ins",
                    "XOR A, Ins","XOR B, Ins","AND A, Ins","AND B, Ins",
                    'INC A', 'INC B', 'INC (Dir)', 'INC (B)','SHL (B), A',"SUB A, Ins","SUB B, Ins","NOT (B), A",
                    'DEC A', 'RET', 'PUSH A', 'PUSH B',
                    'POP A', 'POP B','MOV (Dir), Lit',
                    'MOV (B), Lit',"XOR B, (Dir)","XOR B, (B)","CMP A, (Dir)","CMP A, (B)", "CMP A, Ins",
                    'ADD B, (Dir)','SUB B, (Dir)', "ADD B, (B)", "SUB B, (B)","AND B, (Dir)","OR B, (Dir)","OR B, (B)")

jumps = ("JMP",
         "JEQ", "JNE",
         "JGT", "JLT",
         "JGE", "JLE",
         "JCR",
         "CALL")

not_jumps = ("MOV", "RET", "POP", "PUSH", "ADD", "SUB",
             "AND", "OR", "XOR", "NOT", "SHL", "SHR", "INC",
             "DEC", "CMP", "PUSH", "NOP")

# Argumentos --> Archivo de entrada
input_file = str(argv[1])
# Instrucciones


DARKCYAN_BOLD = '\033[1;36m'
RED_BOLD = '\033[1;91m'
NORMAL_TXT = '\033[0m'


def use_bloody_red_color(text) -> str:
    # return f"{DARKCYAN_BOLD}{text}{NORMAL_TXT}"
    return f"{text}"


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
        raise ValueError(use_bloody_red_color('Algo malo pasó'))

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
        raise ValueError(use_bloody_red_color(
            f"Se intentó convertir '{strange_base_num}' a "
            f"decimal, pero no es base 2, 16 ó 10"))


def procesar_indice(indice: int or str):
    # [Intr, indice, indice]

    # print(f"{RED_BOLD}DEBUG{NORMAL_TXT}")
    # print(f"{RED_BOLD} ~~ {indice} ~~ {NORMAL_TXT}")
    # print(f"{RED_BOLD}DEBUG{NORMAL_TXT}")

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
        raise ValueError(use_bloody_red_color(
            f"El índice '{indice}' no está sorportado"))


def generar_codigo(valor, instruccion):
    # ============================ MARCADOR ============================ ====================================================================================================================================================================================================================================================================================================================
    # FIXME: PLACE HOLDER, ARREGLAR
    # TODO: PLACE HOLDER, ARREGLAR
    # BUG: PLACE HOLDER, ARREGLAR
    # XXX: PLACE HOLDER, ARREGLAR
    # NOTE: PLACE HOLDER, ARREGLAR
    # WARN: PLACE HOLDER, ARREGLAR

    """
    PLACE HOLDER, ARREGLAR
    """

    if "Ins" in instruccion:
        cambiar = 0

        for j in not_jumps:
            if j in instruccion:
                cambiar = 1

        if cambiar:
            instruccion = instruccion.replace("Ins", "Dir")

    else:
        # instruccion = instruccion.replace("Dir", "Ins")
        pass



    if instruccion in opcodes.keys():
        # primeros16 = f'{int(valor):016b}'
        # siguientes20 = (20 - len(opcodes[instruccion])) * '0' + \
        #                opcodes[instruccion]
        # respuesta = primeros16 + siguientes20
        respuesta = f"{int(valor):016b}" \
                    f"{str(opcodes[instruccion]).rjust(20, '0')}"

        return respuesta

    print(instruccion, opcodes)

    raise KeyError(use_bloody_red_color("OPCODE NO ENCONTRADO ERROR"),
                   use_bloody_red_color(instruccion))


def codigo_de_maquina(instruccion,assambler_inst):
    palabra_2 = None
    valor_2 = None

    if instruccion.inst == "NOP":
        instruccion_string = "NOP"
        # resultado = (36 - len(opcodes[instruccion_string])) * '0' + \
        #             opcodes[instruccion_string]
        resultado = f"{str(opcodes[instruccion_string]).rjust(36, '0')}"
        return resultado, instruccion_string

    if instruccion.inst == "RET":
        instruccion_string = "RET"
        # resultado = (36 - len(opcodes[instruccion_string])) * '0' + \
        #             opcodes[instruccion_string]
        resultado = f"{str(opcodes[instruccion_string]).rjust(36, '0')}"
        return resultado, instruccion_string

    if instruccion.inst == "PUSH":
        instruccion_string = "PUSH {}".format(instruccion.in_1)
        # resultado = (36 - len(opcodes[instruccion_string])) * '0' + \
        #             opcodes[instruccion_string]
        resultado = f"{str(opcodes[instruccion_string]).rjust(36, '0')}"
        return resultado, instruccion_string
    if instruccion.inst == "POP":
        instruccion_string = "POP {}".format(instruccion.in_1)
        # resultado = (36 - len(opcodes[instruccion_string])) * '0' + \
        #             opcodes[instruccion_string]
        resultado = f"{str(opcodes[instruccion_string]).rjust(36, '0')}"
        return resultado, instruccion_string
    if instruccion.inst == "INC":
        instruccion_string = "INC {}".format(instruccion.in_1)
        # resultado = (36 - len(opcodes[instruccion_string])) * '0' + \
        #             opcodes[instruccion_string]
        resultado = f"{str(opcodes[instruccion_string]).rjust(36, '0')}"
        return resultado, instruccion_string
    valor_1, palabra_1 = procesar_indice(instruccion.in_1)

    if instruccion.in_2 != '':
        valor_2, palabra_2 = procesar_indice(instruccion.in_2)

    if palabra_1 and palabra_2:

        instruccion_string = f'{assambler_inst} {palabra_1}, {palabra_2}'

        if valor_1 is not None:
            resultado = generar_codigo(valor_1, instruccion_string)

            return resultado, instruccion_string

        elif valor_2 is not None:
            resultado = generar_codigo(valor_2, instruccion_string)

            return resultado, instruccion_string

        elif palabra_1 and palabra_2:
            if instruccion_string not in opcodes.keys():
                print(opcodes)

                raise KeyError(use_bloody_red_color("1NO está en el opcode"),
                               use_bloody_red_color(instruccion_string))

            # resultado = (36 - len(opcodes[instruccion_string])) * \
            #             '0' + opcodes[instruccion_string]
            resultado = f"{str(opcodes[instruccion_string]).rjust(36, '0')}"

            return resultado, instruccion_string

    elif palabra_1:
        instruccion_string = '{} {}'.format(assambler_inst, palabra_1)

        if valor_1 is not None:
            resultado = generar_codigo(valor_1, instruccion_string)

            return resultado, instruccion_string
        elif palabra_1 in REGISTERS:
            return opcodes[instruccion_string].rjust(36, '0'), instruccion_string

        else:

            raise KeyError(use_bloody_red_color("2No está en el opcode"),
                           use_bloody_red_color(instruccion_string))

    else:
        raise KeyError(use_bloody_red_color("Instruccion no permitida"),
                       use_bloody_red_color(instruccion))


for key in label_pairs.keys():
    print(f"{key} {bin(int(label_pairs[key]))} , AAA")


for index, d in enumerate(machiny_stuff):

    if ':' in d.inst:
        resp = d

    else:
        resp, assembly_inst_ = codigo_de_maquina(d, d.inst)
    if d.inst in jumps:
        resp = str(d.in_1) + resp[16:]
    if assembly_inst_ in CASOS_ESPECIALES:
        if assembly_inst_ == "INC (Dir)":
            push_a = (36 - len(opcodes["PUSH A"])) * '0' + opcodes["PUSH A"]
            move_a_lit = '1' + opcodes["MOV A, Lit"]
            move_a_lit = (36 - (len(move_a_lit)))*'0' + move_a_lit
            add_a_dir = (20 - len(opcodes["ADD A, (Dir)"])) * '0' + opcodes["ADD A, (Dir)"]
            add_a_dir = resp[:16] + add_a_dir
            pop_a = opcodes["POP A"].rjust(36, '0')
            pop_a_2 = opcodes["POP A2"].rjust(36, '0')
            total_instrucciones.append(push_a)
            total_instrucciones.append(move_a_lit)
            total_instrucciones.append(add_a_dir)
            total_instrucciones.append(pop_a)
            total_instrucciones.append(pop_a_2)
        elif assembly_inst_ == "INC A":
            add_a_lit = (20 - len(opcodes["ADD A, Lit"])) * '0' + opcodes["ADD A, Lit"]
            add_a_lit = '1' + add_a_lit
            add_a_lit = add_a_lit.rjust(36,'0')
            total_instrucciones.append(add_a_lit)
        elif assembly_inst_ == "DEC A":
            sub_a_lit = (20 - len(opcodes["SUB A, Lit"])) * '0' + opcodes["SUB A, Lit"]
            sub_a_lit = '1' + sub_a_lit
            sub_a_lit = sub_a_lit.rjust(36,'0')
            total_instrucciones.append(sub_a_lit)
        elif assembly_inst_ == "INC B":
            add_b_lit = (20 - len(opcodes["ADD B, Lit"])) * '0' + opcodes["ADD B, Lit"]
            add_b_lit = '1' + add_b_lit
            add_b_lit = add_b_lit.rjust(36,'0')
            total_instrucciones.append(add_b_lit)
        elif assembly_inst_ == "SUB B, Lit":
            total_instrucciones.append(resp)
        elif assembly_inst_ == "MOV (Dir), Lit":
            direccion = f'{int(label_pairs[d.in_1[1:-1]]):016b}'
            valor_ = f'{int(d.in_2):016b}'
            push_a = (36 - len(opcodes["PUSH A"])) * '0' + opcodes["PUSH A"]
            move_a_lit = valor_ + opcodes["MOV A, Lit"].rjust(20, "0")
            move_dir_a = direccion + opcodes["MOV (Dir), A"].rjust(20, "0")
            pop_a = opcodes["POP A"].rjust(36, '0')
            pop_a_2 = opcodes["POP A2"].rjust(36, '0')
            total_instrucciones.append(push_a)
            total_instrucciones.append(move_a_lit)
            total_instrucciones.append(move_dir_a)
            total_instrucciones.append(pop_a)
            total_instrucciones.append(pop_a_2)
        elif assembly_inst_ == "POP A":
            pop_a_2 = opcodes["POP A2"].rjust(36, '0')
            total_instrucciones.append(resp)
            total_instrucciones.append(pop_a_2)
        elif assembly_inst_ == "POP B":
            pop_b_2 = opcodes["POP B2"].rjust(36, '0')
            total_instrucciones.append(resp)
            total_instrucciones.append(pop_b_2)
        elif assembly_inst_ == "RET":
            ret_2 = opcodes["RET 2"].rjust(36, '0')
            total_instrucciones.append(resp)
            total_instrucciones.append(ret_2)
        elif assembly_inst_ == "MOV (B), Lit":
            valor_ = f'{int(d.in_2):016b}'
            push_a = (36 - len(opcodes["PUSH A"])) * '0' + opcodes["PUSH A"]
            move_a_lit = valor_ + opcodes["MOV A, Lit"].rjust(20, "0")
            move_b_dir_a = opcodes["MOV (B), A"].rjust(36, "0")
            pop_a = opcodes["POP A"].rjust(36, '0')
            pop_a_2 = opcodes["POP A2"].rjust(36, '0')
            total_instrucciones.append(push_a)
            total_instrucciones.append(move_a_lit)
            total_instrucciones.append(move_b_dir_a)
            total_instrucciones.append(pop_a)
            total_instrucciones.append(pop_a_2)
        elif assembly_inst_ == "SUB B, (Dir)":
            push_a = (36 - len(opcodes["PUSH A"])) * '0' + opcodes["PUSH A"]
            direccion =  f'{int(label_pairs[d.in_2[1:-1]]):016b}'
            sub_a_dir = (20 - len(opcodes["SUB A, (Dir)"])) * '0' + opcodes["SUB A, (Dir)"]
            sub_a_dir = direccion + sub_a_dir
            mov_b_a = (36 - len(opcodes["MOV B, A"])) * '0' + opcodes["MOV B, A"]
            pop_a = opcodes["POP A"].rjust(36, '0')
            pop_a_2 = opcodes["POP A2"].rjust(36, '0')
            total_instrucciones.append(push_a)
            total_instrucciones.append(sub_a_dir)
            total_instrucciones.append(mov_b_a)
            total_instrucciones.append(pop_a)
            total_instrucciones.append(pop_a_2)
        elif assembly_inst_ == "ADD B, (B)":
            push_a = (36 - len(opcodes["PUSH A"])) * '0' + opcodes["PUSH A"]
            add_a_dir_b = (36 - len(opcodes["ADD A, (B)"])) * '0' + opcodes["ADD A, (B)"]
            mov_b_a = (36 - len(opcodes["MOV B, A"])) * '0' + opcodes["MOV B, A"]
            pop_a = opcodes["POP A"].rjust(36, '0')
            pop_a_2 = opcodes["POP A2"].rjust(36, '0')
            total_instrucciones.append(push_a)
            total_instrucciones.append(add_a_dir_b)
            total_instrucciones.append(mov_b_a)
            total_instrucciones.append(pop_a)
            total_instrucciones.append(pop_a_2)
        elif assembly_inst_ == "SUB B, (B)":
            push_a = (36 - len(opcodes["PUSH A"])) * '0' + opcodes["PUSH A"]
            add_a_dir_b = (36 - len(opcodes["SUB A, (B)"])) * '0' + opcodes["SUB A, (B)"]
            mov_b_a = (36 - len(opcodes["MOV B, A"])) * '0' + opcodes["MOV B, A"]
            pop_a = opcodes["POP A"].rjust(36, '0')
            pop_a_2 = opcodes["POP A2"].rjust(36, '0')
            total_instrucciones.append(push_a)
            total_instrucciones.append(add_a_dir_b)
            total_instrucciones.append(mov_b_a)
            total_instrucciones.append(pop_a)
            total_instrucciones.append(pop_a_2)
        elif assembly_inst_ == "ADD B, (Dir)":
            push_a = (36 - len(opcodes["PUSH A"])) * '0' + opcodes["PUSH A"]
            add_a_dir = (20 - len(opcodes["ADD A, (Dir)"])) * '0' + opcodes["ADD A, (Dir)"]
            add_a_dir = resp[:16] + add_a_dir
            mov_b_a = (36 - len(opcodes["MOV B, A"])) * '0' + opcodes["MOV B, A"]
            pop_a = opcodes["POP A"].rjust(36, '0')
            pop_a_2 = opcodes["POP A2"].rjust(36, '0')
            total_instrucciones.append(push_a)
            total_instrucciones.append(add_a_dir)
            total_instrucciones.append(mov_b_a)
            total_instrucciones.append(pop_a)
            total_instrucciones.append(pop_a_2)
        elif assembly_inst_ == "AND B, (Dir)":
            push_a = (36 - len(opcodes["PUSH A"])) * '0' + opcodes["PUSH A"]
            add_a_dir = (20 - len(opcodes["AND A, (Dir)"])) * '0' + opcodes["AND A, (Dir)"]
            add_a_dir = resp[:16] + add_a_dir
            mov_b_a = (36 - len(opcodes["MOV B, A"])) * '0' + opcodes["MOV B, A"]
            pop_a = opcodes["POP A"].rjust(36, '0')
            pop_a_2 = opcodes["POP A2"].rjust(36, '0')
            total_instrucciones.append(push_a)
            total_instrucciones.append(add_a_dir)
            total_instrucciones.append(mov_b_a)
            total_instrucciones.append(pop_a)
            total_instrucciones.append(pop_a_2)
        elif assembly_inst_ == "AND B, (B)":
            push_a = (36 - len(opcodes["PUSH A"])) * '0' + opcodes["PUSH A"]
            add_a_dir_b = (36 - len(opcodes["AND A, (B)"])) * '0' + opcodes["AND A, (B)"]
            mov_b_a = (36 - len(opcodes["MOV B, A"])) * '0' + opcodes["MOV B, A"]
            pop_a = opcodes["POP A"].rjust(36, '0')
            pop_a_2 = opcodes["POP A2"].rjust(36, '0')
            total_instrucciones.append(push_a)
            total_instrucciones.append(add_a_dir_b)
            total_instrucciones.append(mov_b_a)
            total_instrucciones.append(pop_a)
            total_instrucciones.append(pop_a_2)
        elif assembly_inst_ == "OR B, (B)":
            push_a = (36 - len(opcodes["PUSH A"])) * '0' + opcodes["PUSH A"]
            add_a_dir_b = (36 - len(opcodes["OR A, (B)"])) * '0' + opcodes["OR A, (B)"]
            mov_b_a = (36 - len(opcodes["MOV B, A"])) * '0' + opcodes["MOV B, A"]
            pop_a = opcodes["POP A"].rjust(36, '0')
            pop_a_2 = opcodes["POP A2"].rjust(36, '0')
            total_instrucciones.append(push_a)
            total_instrucciones.append(add_a_dir_b)
            total_instrucciones.append(mov_b_a)
            total_instrucciones.append(pop_a)
            total_instrucciones.append(pop_a_2)
        elif assembly_inst_ == "OR B, (Dir)":
            push_a = (36 - len(opcodes["PUSH A"])) * '0' + opcodes["PUSH A"]
            add_a_dir = (20 - len(opcodes["OR A, (Dir)"])) * '0' + opcodes["OR A, (Dir)"]
            add_a_dir = resp[:16] + add_a_dir
            mov_b_a = (36 - len(opcodes["MOV B, A"])) * '0' + opcodes["MOV B, A"]
            pop_a = opcodes["POP A"].rjust(36, '0')
            pop_a_2 = opcodes["POP A2"].rjust(36, '0')
            total_instrucciones.append(push_a)
            total_instrucciones.append(add_a_dir)
            total_instrucciones.append(mov_b_a)
            total_instrucciones.append(pop_a)
            total_instrucciones.append(pop_a_2)
        elif assembly_inst_ == "XOR B, (Dir)":
            push_a = (36 - len(opcodes["PUSH A"])) * '0' + opcodes["PUSH A"]
            add_a_dir = (20 - len(opcodes["XOR A, (Dir)"])) * '0' + opcodes["XOR A, (Dir)"]
            add_a_dir = resp[:16] + add_a_dir
            mov_b_a = (36 - len(opcodes["MOV B, A"])) * '0' + opcodes["MOV B, A"]
            pop_a = opcodes["POP A"].rjust(36, '0')
            pop_a_2 = opcodes["POP A2"].rjust(36, '0')
            total_instrucciones.append(push_a)
            total_instrucciones.append(add_a_dir)
            total_instrucciones.append(mov_b_a)
            total_instrucciones.append(pop_a)
            total_instrucciones.append(pop_a_2)
        elif assembly_inst_ == "XOR B, (B)":
            push_a = (36 - len(opcodes["PUSH A"])) * '0' + opcodes["PUSH A"]
            add_a_dir_b = (36 - len(opcodes["XOR A, (B)"])) * '0' + opcodes["XOR A, (B)"]
            mov_b_a = (36 - len(opcodes["MOV B, A"])) * '0' + opcodes["MOV B, A"]
            pop_a = opcodes["POP A"].rjust(36, '0')
            pop_a_2 = opcodes["POP A2"].rjust(36, '0')
            total_instrucciones.append(push_a)
            total_instrucciones.append(add_a_dir_b)
            total_instrucciones.append(mov_b_a)
            total_instrucciones.append(pop_a)
            total_instrucciones.append(pop_a_2)
        elif assembly_inst_ == "CMP A, (Dir)":
            raise KeyError("no está la instruccion {}  implementado".format(assembly_inst_))
        elif assembly_inst_ == "CMP A, (B)":
            b_b = (36 - len(opcodes["MOV B, (B)"])) * '0' + opcodes["MOV B, (B)"]
            a_b = (36 - len(opcodes["CMP A, B"])) * '0' + opcodes["CMP A, B"]
            total_instrucciones.append(b_b)
            total_instrucciones.append(a_b)
        elif assembly_inst_ == "CMP A, Ins":
            lit = str(bin(int(label_pairs[d.in_2])))[2:].rjust(16,'0')
            cmp_a_lit = opcodes["CMP A, Ins"].rjust(20,'0')
            cmp_a_lit = lit + cmp_a_lit
            total_instrucciones.append(cmp_a_lit)
        elif assembly_inst_ == "SHR (B), A":
            push_a = (36 - len(opcodes["PUSH A"])) * '0' + opcodes["PUSH A"]
            pop_a = opcodes["POP A"].rjust(36, '0')
            pop_a_2 = opcodes["POP A2"].rjust(36, '0')
            shfr_a = (36 - len(opcodes["SHR A"])) * '0' + opcodes["SHR A"]
            movb_a = (36 - len(opcodes["MOV (B), A"])) * '0' + opcodes["MOV (B), A"]
            total_instrucciones.append(push_a)
            total_instrucciones.append(shfr_a)
            total_instrucciones.append(movb_a)
            total_instrucciones.append(pop_a)
            total_instrucciones.append(pop_a_2)
        elif assembly_inst_ == "ADD A, Ins":
            lit = str(bin(int(label_pairs[d.in_2])))[2:].rjust(16,'0')
            add_a_lit =  (20 - len(opcodes["ADD A, Lit"])) * '0' + opcodes["ADD A, Lit"]
            add_a_lit = lit+add_a_lit
            total_instrucciones.append(add_a_lit)
        elif assembly_inst_ == "ADD B, Ins":
            lit = str(bin(int(label_pairs[d.in_2])))[2:].rjust(16,'0')
            add_a_lit =  (20 - len(opcodes["ADD B, Lit"])) * '0' + opcodes["ADD B, Lit"]
            add_a_lit = lit+add_a_lit
            total_instrucciones.append(add_a_lit)
        elif assembly_inst_ == "OR A, Ins":
            lit = str(bin(int(label_pairs[d.in_2])))[2:].rjust(16,'0')
            add_a_lit =  (20 - len(opcodes["OR A, Lit"])) * '0' + opcodes["OR A, Lit"]
            add_a_lit = lit+add_a_lit
            total_instrucciones.append(add_a_lit)
        elif assembly_inst_ == "OR B, Ins":
            lit = str(bin(int(label_pairs[d.in_2])))[2:].rjust(16,'0')
            add_a_lit =  (20 - len(opcodes["OR B, Lit"])) * '0' + opcodes["OR B, Lit"]
            add_a_lit = lit+add_a_lit
            total_instrucciones.append(add_a_lit)
        elif assembly_inst_ == "XOR A, Ins":
            lit = str(bin(int(label_pairs[d.in_2])))[2:].rjust(16,'0')
            add_a_lit =  (20 - len(opcodes["XOR A, Lit"])) * '0' + opcodes["XOR A, Lit"]
            add_a_lit = lit+add_a_lit
            total_instrucciones.append(add_a_lit)
        elif assembly_inst_ == "XOR B, Ins":
            lit = str(bin(int(label_pairs[d.in_2])))[2:].rjust(16,'0')
            add_a_lit =  (20 - len(opcodes["XOR B, Lit"])) * '0' + opcodes["XOR B, Lit"]
            add_a_lit = lit+add_a_lit
            total_instrucciones.append(add_a_lit)
        elif assembly_inst_ == "AND A, Ins":
            lit = str(bin(int(label_pairs[d.in_2])))[2:].rjust(16,'0')
            add_a_lit =  (20 - len(opcodes["AND A, Lit"])) * '0' + opcodes["AND A, Lit"]
            add_a_lit = lit+add_a_lit
            total_instrucciones.append(add_a_lit)
        elif assembly_inst_ == "AND B, Ins":
            lit = str(bin(int(label_pairs[d.in_2])))[2:].rjust(16,'0')
            add_a_lit =  (20 - len(opcodes["AND B, Lit"])) * '0' + opcodes["AND B, Lit"]
            add_a_lit = lit+add_a_lit
            total_instrucciones.append(add_a_lit)
        elif assembly_inst_ == "SUB A, Ins":
            lit = str(bin(int(label_pairs[d.in_2])))[2:].rjust(16,'0')
            add_a_lit =  (20 - len(opcodes["SUB A, Lit"])) * '0' + opcodes["SUB A, Lit"]
            add_a_lit = lit+add_a_lit
            total_instrucciones.append(add_a_lit)
        elif assembly_inst_ == "SUB B, Ins":
            lit = str(bin(int(label_pairs[d.in_2])))[2:].rjust(16,'0')
            add_a_lit =  (20 - len(opcodes["SUB B, Lit"])) * '0' + opcodes["SUB B, Lit"]
            add_a_lit = lit+add_a_lit
            total_instrucciones.append(add_a_lit)
        elif assembly_inst_ == "SHL (B), A":
            push_a = (36 - len(opcodes["PUSH A"])) * '0' + opcodes["PUSH A"]
            pop_a = opcodes["POP A"].rjust(36, '0')
            pop_a_2 = opcodes["POP A2"].rjust(36, '0')
            shfr_a = (36 - len(opcodes["SHL A"])) * '0' + opcodes["SHL A"]
            movb_a = (36 - len(opcodes["MOV (B), A"])) * '0' + opcodes["MOV (B), A"]
            total_instrucciones.append(push_a)
            total_instrucciones.append(shfr_a)
            total_instrucciones.append(movb_a)
            total_instrucciones.append(pop_a)
            total_instrucciones.append(pop_a_2)
        elif assembly_inst_ == "NOT (B), A":
            push_a = (36 - len(opcodes["PUSH A"])) * '0' + opcodes["PUSH A"]
            pop_a = opcodes["POP A"].rjust(36, '0')
            pop_a_2 = opcodes["POP A2"].rjust(36, '0')
            shfr_a = (36 - len(opcodes["NOT A"])) * '0' + opcodes["NOT A"]
            movb_a = (36 - len(opcodes["MOV (B), A"])) * '0' + opcodes["MOV (B), A"]
            total_instrucciones.append(push_a)
            total_instrucciones.append(shfr_a)
            total_instrucciones.append(movb_a)
            total_instrucciones.append(pop_a)
            total_instrucciones.append(pop_a_2)
        elif assembly_inst_ == "MOV (B), Ins":
            push_a = (36 - len(opcodes["PUSH A"])) * '0' + opcodes["PUSH A"]
            pop_a = opcodes["POP A"].rjust(36, '0')
            pop_a_2 = opcodes["POP A2"].rjust(36, '0')
            lit = str(bin(int(label_pairs[d.in_2])))[2:].rjust(16,'0')
            mov_a_lit =  (20 - len(opcodes["MOV A, Lit"])) * '0' + opcodes["MOV A, Lit"]
            mov_a_lit = lit + mov_a_lit
            mov_b_a =  opcodes["MOV (B), A"].rjust(36, '0')
            total_instrucciones.append(push_a)
            total_instrucciones.append(mov_a_lit)
            total_instrucciones.append(mov_b_a)
            total_instrucciones.append(pop_a)
            total_instrucciones.append(pop_a_2)


    else:
        total_instrucciones.append(resp)
    try:
        print(resp[:16], ' ', resp[16:], ' ', assembly_inst_,
              '|||', d.in_1, d.in_2)
    except:
        print(resp.inst)


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


"""Acá se escriben las instrucciones"""
def conver_hex(binario_string):
    # print(type(hex(int(binario_string, 2))), int(
    #   hex(int(binario_string, 2))), type(int(hex(int(binario_string, 2)))))
    return int(binario_string, 2)

"""
ACA SE ARREGLAN LOS JUMPS
"""
posicion_inst = defaultdict()
for index, inst in enumerate(instrucciones_finales):
    if type(inst)== Instruction:
        posicion_inst[inst.inst] = index
        instrucciones_finales[index]  = '0'.rjust(36, '0')
        print(instrucciones_finales[index])

for index, inst in enumerate(instrucciones_finales):
    print(inst)
    breakpoint()




try:
    rom_programmer = Basys3()
    rom_programmer.begin()
except Exception:
    print("Algo pasó con la placa o no está conectada UwU")
with open("ROM.txt", 'w') as f:

    for index, inst in enumerate(instrucciones_finales):
        f.write(inst)
        # print(inst[:16], ' ', inst[16:], ' ',
        #      instrucciones_finales_string[index])
        lista_hex = [conver_hex(inst[:4]), conver_hex(inst[4:12]),
                     conver_hex(inst[12:20]), conver_hex(inst[20:28]), conver_hex(inst[28:36])]
        lista_hex = bytearray(lista_hex)
        try:
            rom_programmer.write(index, bytearray(lista_hex))
        except Exception:
            print("Algo pasó con la placa o no está conectada UwU")
        f.write('\n')
try:
    rom_programmer.end()
except Exception:
    print("Algo pasó con la placa o no está conectada UwU")

print(" \033[92;1m~~~~~~~~~~~ DATA ~~~~~~~~~~~\033[0m ")
for i in convert_data_entries_to_inst(data): print(i[:16], i[16:])
print(" \033[92;1m~~~~~~~~~~~ CODE ~~~~~~~~~~~\033[0m ")
for i in total_instrucciones: print(i[:16], i[16:])
print(" \033[92;1m~~~~~~~~~~~~~~~~~~~~~~~~~~~~\033[0m ")
print('FIN'); print('😊')
