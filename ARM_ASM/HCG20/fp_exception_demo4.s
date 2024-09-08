.data
a: 
	.float 0.1
b:
        .float 0.2

.global _start

.section .text

_start:
    // Initialize floating-point registers

    // s0 = a
    ldr r3,=a
    vldr.f32 s0,[r3]		

    // s1 = b     
    ldr r3,=b
    vldr.f32 s1,[r3]
    
    movw    r0, #0x0000
    vmsr    fpscr, r0

    vadd.f32 s2, s1, s0

    // Check for floating-point exceptions
    // get a copy of the register to return
    vmrs    r0, fpscr   
    mov     r7, #1      // syscall: exit
    svc     0           // Make syscall

