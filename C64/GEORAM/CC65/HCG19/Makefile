# Where the disk management utility ( from VICE ) is located

export C1541=/Applications/vice-arm64-gtk3-3.6.1/bin/c1541 
# where the CC65 stuff is located. 
# assembler includes
export CA65_INC=/usr/local/Cellar/cc65/2.19/share/cc65/asminc
# libraries
export LD65_LIB=/usr/local/Cellar/cc65/2.19/share/cc65/lib
# linker configurations
export LC65_CFG=/usr/local/Cellar/cc65/2.19/share/cc65/cfg
# C includes
export CC65_INC=/usr/local/Cellar/cc65/2.19/share/cc65/include

geo_struct.prg: geo_struct.o c64-georam.o mandel2.o aux.o
	ld65 -o geo_struct.prg -C c64-asm.cfg  -u __EXEHDR__ --lib c64.lib  geo_struct.o c64-georam.o aux.o -m geo_struct.m

m3.o: m3.c
	cc65 m3.c -t c64 -o m3.o -l m3.l

aux.o: aux.s
	ca65 aux.s -t c64 -o aux.o -l aux.l 
	
geo_struct.o: geo_struct.s macro.s
	ca65 geo_struct.s -t c64 -o geo_struct.o  -l geo_struct.l  

c64-georam.o: c64-georam.s
	ca65 c64-georam.s -t c64 -o c64-georam.o

clean:
	rm -f -v c64-georam.o geo_struct.{o,l,m,prg} aux.{o,l}

