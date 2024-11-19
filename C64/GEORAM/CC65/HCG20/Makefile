# Where the disk management utility ( from VICE ) is located
export C1541=/Users/bigfoot/Desktop/vice-x86-64-gtk3-3.7.1/bin/c1541 
# where the CC65 stuff is located. 
# assembler includes
export CA65_INC=/usr/local/Cellar/cc65/2.19/share/cc65/asminc
# libraries
export LD65_LIB=/usr/local/Cellar/cc65/2.19/share/cc65/lib
# linker configurations
######export LC65_CFG=/usr/local/Cellar/cc65/2.19/share/cc65/cfg

export LC65_CFG=./

# C includes
export CC65_INC=/usr/local/Cellar/cc65/2.19/share/cc65/include

demo.d64: ovrldemo.prg
	$(C1541) -format "georam-test,00" d64 assembler.d64
	$(C1541) -attach assembler.d64 -write ovrldemo
	$(C1541) -attach assembler.d64 -write ovrldemo.1
	$(C1541) -attach assembler.d64 -write ovrldemo.2
	$(C1541) -attach assembler.d64 -write ovrldemo.3
	$(C1541) -attach assembler.d64 -write c64-georam.emd


# main application with overlay modules
overlaydemo.s: overlaydemo.c
	cc65  -t c64 overlaydemo.c -o overlaydemo.s
overlaydemo.o:  overlaydemo.s
	ca65 -o overlaydemo.o overlaydemo.s


# Overaly module
m1.s: m1.c 
	cc65 -t c64 m1.c -o m1.s
m1.o: m1.s 
	ca65 m1.s -o m1.o

m2.s: m2.c 
	cc65 -t c64 m2.c -o m2.s
m2.o: m2.s 
	ca65 m2.s -o m2.o

m3.s: m3.c 
	cc65 -t c64 m3.c -o m3.s
m3.o: m3.s 
	ca65 m3.s -o m3.o

ovrldemo.prg: m1.o m2.o m3.o overlaydemo.o
	ld65  -o ovrldemo -C ./c64-overlay.cfg -m ovrldemo.map m1.o m2.o m3.o overlaydemo.o c64.lib

clean:
	rm -f -v *.o *.s a.out*  *.{1,2,3,4,5,6,7,8,9} *.map ovrldemo
