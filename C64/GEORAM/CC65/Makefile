# Where the disk management utility ( from VICE ) is located
export C1541=/Users/bigfoot/Desktop/vice-x86-64-gtk3-3.7.1/bin/c1541 
# where the CC65 stuff is located. 
# assembler includes
export CA65_INC=/usr/local/Cellar/cc65/2.19/share/cc65/asminc
# libraries
export LD65_LIB=/usr/local/Cellar/cc65/2.19/share/cc65/lib
# linker configurations
export LC65_CFG=/usr/local/Cellar/cc65/2.19/share/cc65/cfg
# C includes
export CC65_INC=/usr/local/Cellar/cc65/2.19/share/cc65/include

demo.d64: print.prg georam.prg
	$(C1541) -format "georam-test,00" d64 assembler.d64
	$(C1541) -attach assembler.d64 -write print.prg
	$(C1541) -attach assembler.d64 -write georam.prg
	$(C1541) -attach assembler.d64 -write c64-georam.emd


# The program that will use the expansion
georam.o: georam.s
	ca65 -t c64 -o georam.o  -l georam.l  georam.s

# driver 
c64-georam.o: c64-georam.s 
	ca65 -t c64 -o c64-georam.o  -l c64-georam.l c64-georam.s

# c64.lib contains the EXEHDR stuff, the c64-asm.cfg contains anything required 
# to correcly produce a working PRG file.
georam.prg: georam.o c64-georam.o 
	ld65 -o georam.prg  -C c64-asm.cfg  -u __EXEHDR__ --lib c64.lib -m georam.m georam.o c64-georam.o 

# 
# HELLO WORLD
#
print.o: print.s
	ca65 print.s -t c64 -o print.o  -l print.l 

print.prg: print.o
	cl65 -o print.prg -u __EXEHDR__ -t c64 -C c64-asm.cfg print.s

clean:
	rm -f -v print.prg assembler.d64 print.l print.m georam.o georam.l c64-georam.o c64-georam.l georam.prg print.o georam.m
