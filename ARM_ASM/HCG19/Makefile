advanced: advanced.o 
	gcc advanced.o -o advanced

advanced.o: advanced.s
	as -g -mfpu=vfpv2 advanced.s -o advanced.o

clean:
	rm advanced.o advanced
