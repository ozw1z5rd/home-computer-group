.export entry
.include "em-kernel.inc"
.include "em-error.inc"
.include "cbm_kernal.inc"
.include "macro.s"

; memory definitions
.include "memory.s"

; the driver functions
.import INSTALL
.import PAGECOUNT
.import MAP
.import COPYFROM
.import COPYTO

.import wait_space
.import printimm
.import wait
.import printhex

.data 

;
; local struct with screen address already
; loaded
;
my_em_copy:
	.tag EM_COPY

;.struct EM_COPY
;        BUF     .addr
;        OFFS    .byte
;        PAGE    .word
;        COUNT   .word
;        UNUSED  .byte
;.endstruct



.code 
.export LOADADDR = *    


;
; code entry point
;

entry:
        jsr printimm
        .byte "georam demo in assembler", 13, "press *space* to continue", 13, 13
	.byte "home computer group 2024", 13, 0 
        jsr wait_space
;
; check for GeoRAM presence
;
	jsr INSTALL
        cpx #EM_ERR_NO_DEVICE
        bne size
        PRINT err_message
        jmp exit
;
; RAM found, get the size
;

size:
        PRINT message
        jsr PAGECOUNT

        tay
        txa
        pha
        tya
        tax
        pla

        jsr $BDCD

        PRINT press_space
        jsr wait_space
	jmp demo

exit:   
        rts




demo:
;
; Inizialize the EM struct
;
	lda #$00
	sta my_em_copy + EM_COPY::BUF
	lda #$04
	sta my_em_copy + EM_COPY::BUF + 1 
	lda #$00
	sta my_em_copy + EM_COPY::OFFS
	sta my_em_copy + EM_COPY::PAGE 
	sta my_em_copy + EM_COPY::PAGE + 1 
	sta my_em_copy + EM_COPY::UNUSED 
	lda #$E8
	sta my_em_copy + EM_COPY::COUNT
	lda #$03	
	sta my_em_copy + EM_COPY::COUNT + 1 

;
; Saves a number of screens into the GeoRAM
;

	ldx #$10
loop_f:

	jsr fill
	lda #19
	jsr CHROUT
	txa
	jsr printhex
	jsr wait
        jsr save_screen
	dex
	bne loop_f

	jsr printimm
	.byte 147, "screens saved on the expansion", 13, "press *space* to replay", 13, 0
	jsr wait_space


;
; Screens replay
;


	ldx #$00
	stx my_em_copy + EM_COPY::PAGE
	stx my_em_copy + EM_COPY::PAGE + 1

	ldx #$10
replay:
	jsr recall_screen
	lda #19
	jsr CHROUT
        txa
	jsr printhex
	jsr wait
	jsr wait
	dex
	bne replay
	jmp exit



;
; Routine to store a screen on the GeoRAM
; the page is incremented after the saving
;

save_screen:
	pha
	txa 
	pha

	lda #<my_em_copy
	ldx #>my_em_copy
	jsr COPYTO

	clc
  	lda my_em_copy + EM_COPY::PAGE
	adc #$04 
	sta my_em_copy + EM_COPY::PAGE

	adc my_em_copy + EM_COPY::PAGE + 1
	sta my_em_copy + EM_COPY::PAGE + 1

	pla
	tax
	pla
	rts

;
; Routine to recall a screen from the GeoRAM
; the page in incremented after the recall
;

recall_screen:

	pha
	txa 
	pha

	lda #<my_em_copy
	ldx #>my_em_copy
	jsr COPYFROM

	clc
  	lda my_em_copy + EM_COPY::PAGE
	adc #$04 
	sta my_em_copy + EM_COPY::PAGE

	adc my_em_copy + EM_COPY::PAGE + 1
	sta my_em_copy + EM_COPY::PAGE + 1

	pla
	tax
	pla
	rts


;
; fill the screen with a single charater
;
         
fill:
	lda #$00
	sta tmp1
	sta tmp2
	sta tmp3
	lda #$ff
	sta tmp4

	lda #$04
	sta tmp1+1
	lda #$05
	sta tmp2+1
	lda #$06
	sta tmp3+1
	sta tmp4+1

	ldy #$00
	txa 
fill_lo1:
	sta (tmp1),y 
	sta (tmp2),y
	sta (tmp3),y
	iny
	bne fill_lo1
	
	ldy #$E8
fill_lo2:
	sta (tmp4),y
	dey 
	bne fill_lo2
	rts

.rodata
message: 
        .asciiz "size in number of 256 bytes pages:" 
err_message:
        .asciiz "no georam found in the system."
press_space:
        .byte 13
        .byte 13
        .asciiz "** press space to continue. **" 
