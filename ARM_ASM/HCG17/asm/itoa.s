.text 
.align 2 
.global _itoa

dumphex:
	push {r0, r1, r2, r3, r5, r6, lr}
	ldr r5, =printbuffer
	ldr r1, =number
	ldr r2, =charmap

	add r1, r1,#3
	mov r6, #0
loop:
	ldrb r0, [r1]
	and r3, r0, #0xf0
	lsr r3, r3, #4
	ldrb r4, [r2,r3]
	strb r4, [r5]
	add r3, r5, #1
	and r3, r0, #0x0f
	ldrb r4, [r2,r3]
	strb r4, [r5]
	add r5, r5, #1
	sub r1, r1, #1
	add r6, r6, #1
	cmp r6, #4
	bne loop 
# write
	mov r7,#4  
	mov r2,#8
	mov r0,#1
	ldr r1,=printbuffer
	svc 0 
	pop {r0, r1, r2, r3, r5, r6, lr}
	bx lr

_itoa:
        push {lr}
	bl dumphex
	pop {pc}

.data
printbuffer:
	.byte 0,0,0,0,0,0,0,0

number:
	.byte 0Xf2, 0Xf3, 0Xfa, 0Xfb

charmap:
	.byte 0x30, 0X31, 0X32, 0X33
	.byte 0X34, 0X35, 0X36, 0X37 
	.byte 0X38, 0X39, 0X41, 0X42
	.byte 0X43, 0X44, 0X45, 0X46

