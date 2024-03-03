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

; $22-$23 text pointer allocates in zp
.define ptext	$22	

entry:  jsr INSTALL 
	cpx #EM_ERR_NO_DEVICE
	bne size

        ldy #<err_message
	sty ptext
	ldy #>err_message
	sty ptext+1
	jsr print
	jmp exit


size:   ldy #<message
	sty ptext
	ldy #>message
	sty ptext+1
	jsr print

pages:  jsr PAGECOUNT
	;
	; swap X and A 
	;
	tay	
	txa
	pha
	tya
        tax
	pla
        ;
	; print A X as unsigned integer 
        ;
	jsr $BDCD		

exit:	rts

print:  ldy #$00 
loop:	lda (ptext), y
	beq done
	jsr CHROUT
	iny
	jmp loop
done:   rts

.rodata

message: 
	.asciiz "size in number of 256bytes pages:"

err_message:
	.asciiz "no georam found in the system."

