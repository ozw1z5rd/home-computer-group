.import _print
.import ptext
;
; PRINT MACRO
;
;  INPUT THE ADDRESS OF THE ZERO TERMINATED STRING
;  OUTPUT THE STRING IS PRINTED ON STDOUT

.macro PRINT string_pointer
        ldy #<(string_pointer-1)
        sty ptext
        ldy #>(string_pointer-1)
        sty ptext+1
        jsr _print
.endmacro


