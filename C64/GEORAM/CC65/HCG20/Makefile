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

demo.d64: georam.prg
	$(C1541) -format "georam-test,00" d64 assembler.d64
	$(C1541) -attach assembler.d64 -write georam.prg
	$(C1541) -attach assembler.d64 -write c64-georam.emd


# main application with overlay modules
overlay_demo.s: overlay_demo.c
	cc65  -t c64 overlay_demo.c -o overlay_demo.s

overlay_demo.o:  overlay_demo.s
	ca65 -o overlay_demo.o overlay_demo.s


# Overaly modules
module1.s: module1.c
	cc65 -t c64 module1.c -o module1.s

module2.s: module2.c
	cc65 module2.c  -o module2.s


module1.o: module1.s
	ca65 -o module1.o module1.s

module2.o: module2.s
	ca65 -o module2.o  module2.s


georam.prg: overlay_demo.o module1.o module2.o
	ld65 -v -C new.cfg  -u __EXEHDR__ -o overaly overlay_demo.o c64.lib 


clean:
	rm -f -v *.o *.s a.out*
