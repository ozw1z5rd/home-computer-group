.data
one: 
	.float 1.0 

.global _start

.section .text

_start:
    // Initialize floating-point registers
    ldr r3,=one

    //  s1 = 1
    vldr.f32 s1,[r3]		
    //  s0 = 1 - 1
    vsub.f32 s0, s1, s1

    // clear the GP STATUS AND CONTROL REGISTER 
    movw    r0, #0x0000
    vmsr    fpscr, r0

    //  s2 = s1 / s0 = 1 / 0 
    vdiv.f32    s2, s1, s0 

    // Check for floating-point exceptions
    // get a copy of the register 
    vmrs    r0, fpscr   
    // The exception about DIV by ZERO is reported in the bit 1
    and     r0, r0, #0x2 
    cmp     r0, #0

    beq     no_divbyzero_exception 

    // in the case of FP_DIVZERO return 1 
    mov     r0, #1      // Return code 1 (indicating an error)
    mov     r7, #1      // syscall: exit
    svc     0           // Make syscall

no_divbyzero_exception:
    // If we reach here, the division did not raise an exception
    mov     r0, #0      // Return code 0
    mov     r7, #1      // syscall: exit
    svc     0           // Make syscall
