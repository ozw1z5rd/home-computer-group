ca65 V2.18 - N/A
Main file   : print.s
Current file: print.s

000000r 1               .export entry
000000r 1               .include "em-kernel.inc"
000000r 2               ;/*****************************************************************************/
000000r 2               ;/*                                                                           */
000000r 2               ;/*                              em-kernel.inc                                */
000000r 2               ;/*                                                                           */
000000r 2               ;/*                           EM kernel interface                             */
000000r 2               ;/*                                                                           */
000000r 2               ;/*                                                                           */
000000r 2               ;/*                                                                           */
000000r 2               ;/* (C) 2002-2003 Ullrich von Bassewitz                                       */
000000r 2               ;/*               Römerstrasse 52                                             */
000000r 2               ;/*               D-70794 Filderstadt                                         */
000000r 2               ;/* EMail:        uz@cc65.org                                                 */
000000r 2               ;/*                                                                           */
000000r 2               ;/*                                                                           */
000000r 2               ;/* This software is provided 'as-is', without any expressed or implied       */
000000r 2               ;/* warranty.  In no event will the authors be held liable for any damages    */
000000r 2               ;/* arising from the use of this software.                                    */
000000r 2               ;/*                                                                           */
000000r 2               ;/* Permission is granted to anyone to use this software for any purpose,     */
000000r 2               ;/* including commercial applications, and to alter it and redistribute it    */
000000r 2               ;/* freely, subject to the following restrictions:                            */
000000r 2               ;/*                                                                           */
000000r 2               ;/* 1. The origin of this software must not be misrepresented; you must not   */
000000r 2               ;/*    claim that you wrote the original software. If you use this software   */
000000r 2               ;/*    in a product, an acknowledgment in the product documentation would be  */
000000r 2               ;/*    appreciated but is not required.                                       */
000000r 2               ;/* 2. Altered source versions must be plainly marked as such, and must not   */
000000r 2               ;/*    be misrepresented as being the original software.                      */
000000r 2               ;/* 3. This notice may not be removed or altered from any source              */
000000r 2               ;/*    distribution.                                                          */
000000r 2               ;/*                                                                           */
000000r 2               ;/*****************************************************************************/
000000r 2               
000000r 2               
000000r 2               
000000r 2               ;------------------------------------------------------------------------------
000000r 2               ; The driver header
000000r 2               
000000r 2               .struct EMD_HDR
000000r 2                       ID      .byte   3       ; Contains 0x65, 0x6d, 0x64 ("emd")
000000r 2                       VERSION .byte   1       ; Interface version
000000r 2                       LIBREF  .addr           ; Library reference
000000r 2                       JUMPTAB .struct
000000r 2                           INSTALL     .addr   ; INSTALL routine
000000r 2                           UNINSTALL   .addr   ; UNINSTALL routine
000000r 2                           PAGECOUNT   .addr   ; PAGECOUNT routine
000000r 2                           MAP         .addr   ; MAP routine
000000r 2                           USE         .addr   ; USE routine
000000r 2                           MAPCLEAN    .addr   ; MAPCLEAN routine
000000r 2                           COPYFROM    .addr   ; COPYFROM routine
000000r 2                           COPYTO      .addr   ; COPYTO routine
000000r 2                       .endstruct
000000r 2               .endstruct
000000r 2               
000000r 2               ;------------------------------------------------------------------------------
000000r 2               ; The EMD API version, stored in EMD_HDR::VERSION
000000r 2               
000000r 2               EMD_API_VERSION         = $02
000000r 2               
000000r 2               ;------------------------------------------------------------------------------
000000r 2               ; The asm equivalent to the C em_copy structure
000000r 2               
000000r 2               .struct EM_COPY
000000r 2                       BUF     .addr           ; Memory buffer to copy from or to
000000r 2                       OFFS    .byte           ; Offset into page
000000r 2                       PAGE    .word           ; Starting page to copy from or to
000000r 2                       COUNT   .word           ; Number of bytes to copy
000000r 2                       UNUSED  .byte           ; Make the size 8 bytes
000000r 2               .endstruct
000000r 2               
000000r 2               ;------------------------------------------------------------------------------
000000r 2               ; Variables
000000r 2               
000000r 2                       .global _em_drv                         ; Pointer to driver
000000r 2               
000000r 2               ;------------------------------------------------------------------------------
000000r 2               ; Driver entry points
000000r 2               
000000r 2                       .global emd_install
000000r 2                       .global emd_uninstall
000000r 2                       .global emd_pagecount
000000r 2                       .global emd_map
000000r 2                       .global emd_use
000000r 2                       .global emd_commit
000000r 2                       .global emd_copyfrom
000000r 2                       .global emd_copyto
000000r 2               
000000r 2               ;------------------------------------------------------------------------------
000000r 2               ; ASM functions
000000r 2               
000000r 2                       .global em_clear_ptr
000000r 2               
000000r 2               ;------------------------------------------------------------------------------
000000r 2               ; C callable functions
000000r 2               
000000r 2                       .global _em_load_driver
000000r 2                       .global _em_unload
000000r 2                       .global _em_install
000000r 2                       .global _em_uninstall
000000r 2                       .global _em_pagecount
000000r 2                       .global _em_map
000000r 2                       .global _em_use
000000r 2                       .global _em_commit
000000r 2                       .global _em_copyfrom
000000r 2                       .global _em_copyto
000000r 2               
000000r 2               
000000r 1               .include "em-error.inc"
000000r 2               ;/*****************************************************************************/
000000r 2               ;/*                                                                           */
000000r 2               ;/*                               em-error.inc                                */
000000r 2               ;/*                                                                           */
000000r 2               ;/*                              EM error codes                               */
000000r 2               ;/*                                                                           */
000000r 2               ;/*                                                                           */
000000r 2               ;/*                                                                           */
000000r 2               ;/* (C) 2002-2012, Ullrich von Bassewitz                                      */
000000r 2               ;/*                Roemerstrasse 52                                           */
000000r 2               ;/*                D-70794 Filderstadt                                        */
000000r 2               ;/* EMail:         uz@cc65.org                                                */
000000r 2               ;/*                                                                           */
000000r 2               ;/*                                                                           */
000000r 2               ;/* This software is provided 'as-is', without any expressed or implied       */
000000r 2               ;/* warranty.  In no event will the authors be held liable for any damages    */
000000r 2               ;/* arising from the use of this software.                                    */
000000r 2               ;/*                                                                           */
000000r 2               ;/* Permission is granted to anyone to use this software for any purpose,     */
000000r 2               ;/* including commercial applications, and to alter it and redistribute it    */
000000r 2               ;/* freely, subject to the following restrictions:                            */
000000r 2               ;/*                                                                           */
000000r 2               ;/* 1. The origin of this software must not be misrepresented; you must not   */
000000r 2               ;/*    claim that you wrote the original software. If you use this software   */
000000r 2               ;/*    in a product, an acknowledgment in the product documentation would be  */
000000r 2               ;/*    appreciated but is not required.                                       */
000000r 2               ;/* 2. Altered source versions must be plainly marked as such, and must not   */
000000r 2               ;/*    be misrepresented as being the original software.                      */
000000r 2               ;/* 3. This notice may not be removed or altered from any source              */
000000r 2               ;/*    distribution.                                                          */
000000r 2               ;/*                                                                           */
000000r 2               ;/*****************************************************************************/
000000r 2               
000000r 2               
000000r 2               
000000r 2               ; Error constants
000000r 2               .enum
000000r 2                       EM_ERR_OK                       ; No error
000000r 2                       EM_ERR_NO_DRIVER                ; No driver available
000000r 2                       EM_ERR_CANNOT_LOAD              ; Error loading driver
000000r 2                       EM_ERR_INV_DRIVER               ; Invalid driver
000000r 2                       EM_ERR_NO_DEVICE                ; Device (hardware) not found
000000r 2                       EM_ERR_INSTALLED                ; A driver is already installed
000000r 2               
000000r 2                       EM_ERR_COUNT                    ; Special: Number of error messages
000000r 2               .endenum
000000r 2               
000000r 2               
000000r 2               
000000r 2               
000000r 1               .include "cbm_kernal.inc"
000000r 2               ;
000000r 2               ; Olli Savia <ops@iki.fi>
000000r 2               ; Greg King
000000r 2               ;
000000r 2               ; Commodore-compatibles Kernal functions
000000r 2               ;
000000r 2               
000000r 2               .if .def(__CX16__)
000000r 2                 ; CX16 extended jump table
000000r 2                 ENTROPY_GET                   := $FECF
000000r 2                 KEYBRD_BUF_PUT                := $FED2
000000r 2                 CONSOLE_SET_PAGE_MSG          := $FED5
000000r 2                 CONSOLE_PUT_IMAGE             := $FED8
000000r 2                 CONSOLE_INIT                  := $FEDB
000000r 2                 CONSOLE_PUT_CHAR              := $FEDE
000000r 2                 CONSOLE_GET_CHAR              := $FEE1
000000r 2                 MEMORY_FILL                   := $FEE4
000000r 2                 MEMORY_COPY                   := $FEE7
000000r 2                 MEMORY_CRC                    := $FEEA
000000r 2                 MEMORY_DECOMPRESS             := $FEED
000000r 2                 SPRITE_SET_IMAGE              := $FEF0
000000r 2                 SPRITE_SET_POSITION           := $FEF3
000000r 2                 FB_INIT                       := $FEF6
000000r 2                 FB_GET_INFO                   := $FEF9
000000r 2                 FB_SET_PALETTE                := $FEFC
000000r 2                 FB_CURSOR_POSITION            := $FEFF
000000r 2                 FB_CURSOR_NEXT_LINE           := $FF02
000000r 2                 FB_GET_PIXEL                  := $FF05
000000r 2                 FB_GET_PIXELS                 := $FF08
000000r 2                 FB_SET_PIXEL                  := $FF0B
000000r 2                 FB_SET_PIXELS                 := $FF0E
000000r 2                 FB_SET_8_PIXELS               := $FF11
000000r 2                 FB_SET_8_PIXELS_OPAQUE        := $FF14
000000r 2                 FB_FILL_PIXELS                := $FF17
000000r 2                 FB_FILTER_PIXELS              := $FF1A
000000r 2                 FB_MOVE_PIXELS                := $FF1D
000000r 2                 GRAPH_INIT                    := $FF20
000000r 2                 GRAPH_CLEAR                   := $FF23
000000r 2                 GRAPH_SET_WINDOW              := $FF26
000000r 2                 GRAPH_SET_COLORS              := $FF29
000000r 2                 GRAPH_DRAW_LINE               := $FF2C
000000r 2                 GRAPH_DRAW_RECT               := $FF2F
000000r 2                 GRAPH_MOVE_RECT               := $FF32
000000r 2                 GRAPH_DRAW_OVAL               := $FF35
000000r 2                 GRAPH_DRAW_IMAGE              := $FF38
000000r 2                 GRAPH_SET_FONT                := $FF3B
000000r 2                 GRAPH_GET_CHAR_SIZE           := $FF3E
000000r 2                 GRAPH_PUT_CHAR                := $FF41
000000r 2                 RESTORE_BASIC                 := $FF47
000000r 2                 CLOCK_SET_DATE_TIME           := $FF4D
000000r 2                 CLOCK_GET_DATE_TIME           := $FF50
000000r 2                 JOYSTICK_SCAN                 := $FF53
000000r 2                 JOYSTICK_GET                  := $FF56
000000r 2                 SCREEN_SET_MODE               := $FF5F
000000r 2                 SCREEN_SET_CHARSET            := $FF62
000000r 2                 MOUSE_CONFIG                  := $FF68
000000r 2                 MOUSE_GET                     := $FF6B
000000r 2               .endif
000000r 2               
000000r 2               .if .def(__C128__)
000000r 2                 ; C128 extended jump table
000000r 2                 C64MODE      := $FF4D
000000r 2                 SWAPPER      := $FF5F
000000r 2                 SETBNK       := $FF68
000000r 2               .endif
000000r 2               
000000r 2               .if .def(__C128__) || .def(__CX16__)
000000r 2                 ; Extended jump table
000000r 2                 CLSALL       := $FF4A
000000r 2                 LKUPLA       := $FF59
000000r 2                 LKUPSA       := $FF5C
000000r 2                 PFKEY        := $FF65
000000r 2                 JSRFAR       := $FF6E
000000r 2                 INDFET       := $FF74
000000r 2                 INDSTA       := $FF77
000000r 2                 INDCMP       := $FF7A
000000r 2                 PRIMM        := $FF7D
000000r 2               .endif
000000r 2               
000000r 2               .if .def(__C64__) || .def(__C128__) || .def(__C16__) || .def(__CX16__)
000000r 2                 CINT         := $FF81
000000r 2                 IOINIT       := $FF84
000000r 2                 RAMTAS       := $FF87
000000r 2               .elseif .def(__VIC20__)
000000r 2                 CINT         := $E518         ; No entries are in the Kernal jump table of the VIC-20 for these three (3) functions.
000000r 2                 IOINIT       := $FDF9         ; The entries for these functions have been set to point directly to the functions
000000r 2                 RAMTAS       := $FD8D         ; in the Kernal, to maintain compatibility with the other Commodore platforms.
000000r 2               .elseif .def(__CBM510__) || .def(__CBM610__)
000000r 2                 IOINIT       := $FF7B
000000r 2                 CINT         := $FF7E
000000r 2               .endif
000000r 2               
000000r 2               .if .def(__VIC20__) || .def(__C64__) || .def(__C128__) || .def(__C16__) || .def(__CX16__)
000000r 2                 RESTOR       := $FF8A
000000r 2                 VECTOR       := $FF8D
000000r 2               .elseif .def(__CBM510__) || .def(__CBM610__)
000000r 2                 VECTOR       := $FF84
000000r 2                 RESTOR       := $FF87
000000r 2               .endif
000000r 2               
000000r 2               .if .def(__CBM510__) || .def(__CBM610__) || .def(__VIC20__) || .def(__C64__) || .def(__C128__) || .def(__C16__) || .def(__CX16__)
000000r 2                 SETMSG       := $FF90
000000r 2                 SECOND       := $FF93
000000r 2                 TKSA         := $FF96
000000r 2                 MEMTOP       := $FF99
000000r 2                 MEMBOT       := $FF9C
000000r 2                 SCNKEY       := $FF9F
000000r 2                 SETTMO       := $FFA2
000000r 2                 ACPTR        := $FFA5
000000r 2                 CIOUT        := $FFA8
000000r 2                 UNTLK        := $FFAB
000000r 2                 UNLSN        := $FFAE
000000r 2                 LISTEN       := $FFB1
000000r 2                 TALK         := $FFB4
000000r 2                 READST       := $FFB7
000000r 2                 SETLFS       := $FFBA
000000r 2                 SETNAM       := $FFBD
000000r 2                 OPEN         := $FFC0
000000r 2                 CLOSE        := $FFC3
000000r 2               .endif
000000r 2               
000000r 2               ; Available on all platforms including PET
000000r 2               CHKIN          := $FFC6
000000r 2               CKOUT          := $FFC9
000000r 2               CHKOUT         := $FFC9
000000r 2               CLRCH          := $FFCC
000000r 2               CLRCHN         := $FFCC
000000r 2               BASIN          := $FFCF
000000r 2               CHRIN          := $FFCF
000000r 2               BSOUT          := $FFD2
000000r 2               CHROUT         := $FFD2
000000r 2               
000000r 2               .if .def(__CBM510__) || .def(__CBM610__) || .def(__VIC20__) || .def(__C64__) || .def(__C128__) || .def(__C16__) || .def(__CX16__)
000000r 2                 LOAD         := $FFD5
000000r 2                 SAVE         := $FFD8
000000r 2                 SETTIM       := $FFDB
000000r 2                 RDTIM        := $FFDE
000000r 2               .endif
000000r 2               
000000r 2               ; Available on all platforms including PET
000000r 2               STOP           := $FFE1
000000r 2               GETIN          := $FFE4
000000r 2               CLALL          := $FFE7
000000r 2               UDTIM          := $FFEA
000000r 2               
000000r 2               .if .def(__CBM510__) || .def(__CBM610__) || .def(__VIC20__) || .def(__C64__) || .def(__C128__) || .def(__C16__) || .def(__CX16__)
000000r 2                 SCREEN       := $FFED
000000r 2                 PLOT         := $FFF0
000000r 2                 IOBASE       := $FFF3
000000r 2               .endif
000000r 2               
000000r 2               ; ---------------------------------------------------------------------------
000000r 2               ; Kernal routines, direct entries
000000r 2               ;
000000r 2               ; Unlike the above, these are not standard functions with entries in the jump
000000r 2               ; table. They do not exist in all Kernals, and where they do the entry point is
000000r 2               ; specific to that particular machine and possibly even Kernal version.
000000r 2               ;
000000r 2               ; This list is not comprehensive: missing items for particular machines
000000r 2               ; should be added as needed.
000000r 2               ;
000000r 2               ; UPDCRAMPTR: Updates the color RAM pointer to match the screen RAM pointer.
000000r 2               ;
000000r 2               
000000r 2               .if .def(__VIC20__)
000000r 2                 CLRSCR       := $E55F
000000r 2                 KBDREAD      := $E5CF
000000r 2                 UPDCRAMPTR   := $EAB2
000000r 2               .elseif .def(__C64__)
000000r 2                 CLRSCR       := $E544
000000r 2                 KBDREAD      := $E5B4
000000r 2                 NMIEXIT      := $FEBC
000000r 2                 UPDCRAMPTR   := $EA24
000000r 2               .elseif .def(__C128__)
000000r 2                 CLRSCR       := $C142
000000r 2                 KBDREAD      := $C006
000000r 2                 NMIEXIT      := $FF33
000000r 2                 NEWLINE      := $C363
000000r 2                 PRINT        := $C322
000000r 2                 CURS_SET     := $CD57
000000r 2                 CURS_ON      := $CD6F
000000r 2                 CURS_OFF     := $CD9F
000000r 2               .elseif .def(__C16__)
000000r 2                 CLRSCR       := $D88B
000000r 2                 KBDREAD      := $D8C1
000000r 2               .endif
000000r 2               
000000r 1               
000000r 1               
000000r 1               .data
000000r 1               
000000r 1               .struct MY_EM_COPY
000000r 1                       BUF     .addr
000000r 1                       OFFS    .byte
000000r 1                       PAGE    .word
000000r 1                       COUNT   .word
000000r 1                       UNUSED  .byte
000000r 1               .endstruct
000000r 1               
000000r 1               
000000r 1               .code
000000r 1               
000000r 1               .export LOADADDR = *
000000r 1               
000000r 1               entry:
000000r 1  A0 00        	ldy #$00
000002r 1               
000002r 1               loop:
000002r 1  B9 rr rr     	lda message, y
000005r 1  F0 07        	beq exit
000007r 1  20 D2 FF     	jsr $FFD2
00000Ar 1  C8           	iny
00000Br 1  4C rr rr     	jmp loop
00000Er 1               
00000Er 1               exit:
00000Er 1  60           	rts
00000Fr 1               
00000Fr 1               .segment "RODATA"
000000r 1               message:
000000r 1  48 45 4C 4C  	.asciiz "hello world"
000004r 1  4F 20 57 4F  
000008r 1  52 4C 44 00  
00000Cr 1               
00000Cr 1               
00000Cr 1               
