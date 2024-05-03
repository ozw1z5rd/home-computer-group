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

# HELLO WORLD
#
print.o: print.s
	ca65 print.s -t c64 -o print.o  -l print.l  

print.prg: print.o
	cl65 -o print.prg -u __EXEHDR__ -t c64 -C c64-asm.cfg print.o -m print.m

clean:
	rm -f -v print.prg print.l print.m print.o 
