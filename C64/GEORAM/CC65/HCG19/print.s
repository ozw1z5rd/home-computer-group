.export entry
.include "em-kernel.inc"
.include "em-error.inc"
.include "cbm_kernal.inc"


.data 

.struct MY_EM_COPY
        BUF     .addr   
        OFFS    .byte  
        PAGE    .word 
        COUNT   .word
        UNUSED  .byte
.endstruct


.code 

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


