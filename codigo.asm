DATA:

 mul_uno 2
 mul_dos 3
 resultado 0
 ;resultado_antiguo 0

CODE:
 MOV A,0
 MOV B,0
 JMP main
 ; for(mul_dos>=0;mul_dos--){
 ; res_antiguo = resultado;
 ; resultado += mul_uno;
 ; if (resultado<res_antiguo){
 ; resultado = res_antiguo;
 ; exit 1;}}

main:
 MOV A,(mul_dos)
 CMP A,0
 JEQ done
while:
 MOV A,(resultado)
 ;MOV (resultado_antiguo),A

 ADD A,(mul_uno)
if:; revisar overflow
;si es overflow, será valor maximo (2**16)-1
endif:
;fin overlow
 MOV (resultado),A
 MOV A,(mul_dos)
 DEC A
 MOV (mul_dos),A

 CMP A,0
 JNE while

done:
 JMP end
end:
