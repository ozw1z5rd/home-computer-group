.data
// the lowest normalized number you can achieve
// with a 32bit floating point number
a: 
	.float 1.1754943508e-38
b:

	.float 1.1754943508e+38

.global _start

.section .text

_start:
	// Initialize floating-point	
	// s0 = a
	ldr r3,=a
	vldr.f32 s0,[r3]		

	ldr r3,=b
        vldr.f32 s1, [r3]

	mov    r0, #0
	vmsr    fpscr, r0

	vdiv.f32 s2, s0, s1

	// Check for floating-point exceptions
	// get a copy of the register to return
	vmrs    r0, fpscr   
	mov     r7, #1      // syscall: exit
	svc     0           // Make syscall
