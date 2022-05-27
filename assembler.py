from sys import argv
from iic2343 import Basys3
rom_programmer = Basys3()

ARGUMENTO = str(argv[1])


def leyendo_datos(linea):
    linea
    pass


def leyendo_subrutina(linea):
    pass


def leyendo_codigo(linea):
    pass


def leyendo_instruccion(instr, a=None, b=None):
    pass


contenido = []
with open(ARGUMENTO, "r", newline="") as file:
    for linea in file:
        print(linea)
