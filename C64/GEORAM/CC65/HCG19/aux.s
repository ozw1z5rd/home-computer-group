; You need to provide these externally
.include "cbm_kernal.inc"

;
; memory defs shared among
; all the modules
.include "memory.s"

.export _print
.export printchar
.export printhex
.export printimm
.export printnewline
.export wait_space
.export wait

.code

;
; local print function
; ptext -> zerp page pointer to the zero terminated
; string. Max length = 255
;
; outputs the chars on STDOUT
;
_print:  
        ldy #$01 		; the ptext point a byte before the string
loop:   
        lda (ptext), y
        beq done
        jsr CHROUT
        iny
        jmp loop
done:   
        rts
 
;
; Waits space
;
wait_space:
        lda $DC01
        cmp #$ef
        bne wait_space
        rts


;
; Wait a little
;
wait:
	pha
	txa
	pha

	lda #$ff
a_loop:
	ldx #$ff
x_loop:
	dex
	bne x_loop

	sbc #$01
	bne a_loop

	pla
	tax
	pla
	rts
	
;
; Print a character, ASCII code in A
;
printchar:
	jsr CHROUT	
	rts

;
; Print a null-terminated string that's inline following the jsr call
;
printimm:
	pla		; Take the low addr
	sta ptext	; store it
	pla		; Take the hi addr
	sta ptext+1	; store it
	jsr _print 
	; now y is the length of the string
	; add this value to the current address 
	; to get the return address
	clc
	tya
	adc ptext
	tay
        lda #$00
	adc ptext+1
	pha
        tya 
        pha
	rts


;
; print an hexdecimal number
;
printhex:
	pha
	ror
	ror 
	ror 
	ror
	jsr printnybble
	pla

;
; print a nibble ( the lower 4 birs in A )
;
printnybble:
	pha
	and #15
	cmp #10
	bmi skipletter
	adc #6

;
; Convert the value into a printable
;
skipletter:
	adc #48
	jsr printchar
	pla
	rts

;
; print space
;
printspace:
	lda #' '
	jmp printchar


;
; carrige return
;
printnewline:
	jsr printimm
	.byte 13,0
	rts

    	
