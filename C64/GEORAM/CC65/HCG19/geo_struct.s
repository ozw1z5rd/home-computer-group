.export entry
.include "em-kernel.inc"
.include "em-error.inc"
.include "cbm_kernal.inc"

; the driver functions
.import INSTALL
.import PAGECOUNT
.import MAP
.import COPYFROM
.import COPYTO


.data 

; local struct 
.struct MY_EM_COPY
        BUF     .addr   
        OFFS    .byte  
        PAGE    .word 
        COUNT   .word
        UNUSED  .byte
.endstruct



;
; PRINT MACRO
;
;  INPUT THE ADDRESS OF THE ZERO TERMINATED STRING
;  OUTPUT THE STRING IS PRINTED ON STDOUT

.macro PRINT string_pointer
        ldy #<string_pointer
        sty ptext
        ldy #>string_pointer
        sty ptext+1
        jsr _print
.endmacro

; zero page text pointer for the print function 
.define ptext $22 


.code 
.export LOADADDR = *    


;
; code entry point
;

entry:
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

exit:   
        rts
        
;
; local print function
; ptext -> zerp page pointer to the zero terminated
; string. Max length = 255
;
; outputs the chars on STDOUT
;
_print:  
        ldy #$00 
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




.rodata
message: 
        .asciiz "size in number of 256 bytes pages:" 
err_message:
        .asciiz "no georam found in the system."
press_space:
        .byte 13
        .byte 13
        .asciiz "** press space to continue. **" 
