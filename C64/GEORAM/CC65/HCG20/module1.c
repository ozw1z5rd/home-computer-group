#include <stdio.h> 
#include <stdlib.h> 
#include <fcntl.h>
#include <unistd.h>

#pragma code-name ("OVERLAY1");
#pragma rodata-name ("OVERLAY1");

int overlay1() { 
    printf("This is overaly 1.\n"); 
    return 1;
}
