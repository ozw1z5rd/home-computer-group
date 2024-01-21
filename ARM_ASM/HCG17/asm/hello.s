.extern _itoa
.global _start 

_start:
	mov r0, #1
	ldr r1, =message
	ldr r2, =len
	mov r7, #4
	swi 0
        bl _itoa 
	mov r7,#1
	swi 0 


.data 
message:
	.ascii "hello world.\n"
len = .-message
