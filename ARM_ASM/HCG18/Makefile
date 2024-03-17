float: float.o 
	gcc float.o -o float

float.o: float.s 
	as -g -mfpu=vfpv2 float.s -o float.o

clean:
	rm float.o float
