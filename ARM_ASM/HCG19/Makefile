advanced: advanced.o 
	gcc advanced.o -o advanced

minmax.o: minmax.s
	as -g -mfpu=vfpv2 minmax.s -o minmax.o

minmax: minmax.o
	gcc minmax.o -o minmax

advanced.o: advanced.s
	as -g -mfpu=vfpv2 advanced.s -o advanced.o

clean:
	rm advanced.o advanced minmax.o minmax
