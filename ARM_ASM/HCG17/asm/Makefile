hello: hello.o itoa.o
	ld hello.o itoa.o -o hello

hello.o: hello.s
	as -g hello.s -o hello.o

itoa.o: itoa.s
	as -g itoa.s -o itoa.o

clean:
	rm hello.o hello itoa.o
