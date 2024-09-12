.data
a: 
	.float -4.0

.global _start

.section .text

_start:
    // Initialize floating-point registers

    // s0 = a
    ldr r3,=a
    vldr.f32 s0,[r3]		

    movw    r0, #0x0000
    vmsr    fpscr, r0

    vsqrt.f32 s2, s0


    // Check for floating-point exceptions
    // get a copy of the register to return
    vmrs    r0, fpscr   
    mov     r7, #1      // syscall: exit
    svc     0           // Make syscall

