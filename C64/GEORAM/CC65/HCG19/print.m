Modules list:
-------------
print.o:
    CODE              Offs=000000  Size=00000F  Align=00001  Fill=0000
    RODATA            Offs=000000  Size=00000C  Align=00001  Fill=0000
/usr/local/Cellar/cc65/2.19/share/cc65/lib/c64.lib(exehdr.o):
    EXEHDR            Offs=000000  Size=00000C  Align=00001  Fill=0000
/usr/local/Cellar/cc65/2.19/share/cc65/lib/c64.lib(loadaddr.o):
    LOADADDR          Offs=000000  Size=000002  Align=00001  Fill=0000


Segment list:
-------------
Name                   Start     End    Size  Align
----------------------------------------------------
LOADADDR              0007FF  000800  000002  00001
EXEHDR                000801  00080C  00000C  00001
CODE                  00080D  00081B  00000F  00001
RODATA                00081C  000827  00000C  00001


Exports list by name:
---------------------
__EXEHDR__                000001 REA    __LOADADDR__              000001 REA    



Exports list by value:
----------------------
__EXEHDR__                000001 REA    __LOADADDR__              000001 REA    



Imports list:
-------------
__EXEHDR__ (exehdr.o):
    [linker generated]       
__LOADADDR__ (loadaddr.o):
    [linker generated]        /usr/local/Cellar/cc65/2.19/share/cc65/cfg/c64-asm.cfg(5)

