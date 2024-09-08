.data
// the lowest normalized number you can achieve
// with a 32bit floating point number
a: 
	.float 1.0e-40  

.global _start

.section .text

_start:
	// DO NOTHING, TO DEMO AVAILABLE 

	// Check for floating-point exceptions
	// get a copy of the register to return
	vmrs    r0, fpscr   
	mov     r7, #1      // syscall: exit
	svc     0           // Make syscall
