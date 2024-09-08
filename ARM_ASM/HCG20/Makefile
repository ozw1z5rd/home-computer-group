# List of source files
SRC = fp_exception_demo3.s fp_exception_demo4.s fp_exception_demo5.s fp_exception_demo6.s fp_exception_demo7.s 

# Corresponding object files
OBJ = $(SRC:.s=.o)

# Corresponding target executables
TARGETS = $(SRC:.s=)

# Assembler and linker
AS = as
LD = ld 
ASFLAG = -g -mfpu=vfpv2

# Default target
all: $(TARGETS) floating_point_exception_demo fp_exception_demo2


floating_point_exception_demo: 
	gcc floating_point_exception_demo.c -o floating_point_exception_demo 

fp_exception_demo2:
	gcc fp_exception_demo2.c -o fp_exception_demo2 

# Rule to create each executable from its corresponding object file
%: %.o
	@echo "Linking $< to $@"
	$(LD) -o $@ $< 

# Rule to assemble each source file into an object file
$(OBJ): $(SRC)
	@echo "Assembling $< to $@"
	$(AS) $(ASFLAG) $< -o $@ 

# Clean up generated files
clean:
	rm -f $(OBJ) $(TARGETS) fp_exception_demo2 floating_point_exception_demo

