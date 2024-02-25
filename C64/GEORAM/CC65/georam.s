.export entry
.include "em-kernel.inc"
.include "em-error.inc"
.include "cbm_kernal.inc"


.code

.import INSTALL
.import PAGECOUNT
.import MAP
.import COPYFROM
.import COPYTO

.export LOADADDR = *	

entry:
        jsr INSTALL 
	ldy #$00

loop:
	lda message, y
	beq exit
	jsr CHROUT
	iny
	jmp loop

exit:
	rts

.rodata

message: 
	.asciiz "hello world"


