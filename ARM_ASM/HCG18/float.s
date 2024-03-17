    .data
PI:
    .double 3.141592756

strfdouble:
    .asciz  "pi=%f\n"

    .text
    .align  2
    .global main

main:
    push        {r1,r2,r3,lr}
    ldr         r3, =PI

    #
    # vldr will load 64 bit data ( double ) 
    # from the address pointed by r3
    #
    vldr.64     d7, [r3]
    #
    # d7 = d7 + d7 
    #
    vadd.f64    d7, d7, d7
    #
    # the double value is splitted in two
    # parts for the r2 and r3 registers
    #
    vmov        r2, r3, d7
    ldr         r0, =strfdouble
    bl          printf

    pop         {r1,r2,r3,lr} 
    mov         r0, #1
    bx          lr 
