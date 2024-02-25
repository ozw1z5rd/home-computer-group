.export entry
.segment "CODE"

.export LOADADDR = *	

entry:
	ldy #$00

loop:
	lda message, y
	beq exit
	jsr $FFD2
	iny
	jmp loop

exit:
	rts

.segment "RODATA"
message: 
	.asciiz "hello world"


