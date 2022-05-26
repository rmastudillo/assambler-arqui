from sys import argv

ARGUMENTO = str(argv[1])
contenido = []
with open(ARGUMENTO, "r") as file:
    for linea in file:
        if "//" in linea:
            linea = linea.split("//")[0]
        linea = linea.replace("\t", " ")
        linea = linea.strip("\n").strip(" ")
        if linea and (linea[0:2] != '//'):
            contenido.append(linea)
for linea in contenido:
    uf 
