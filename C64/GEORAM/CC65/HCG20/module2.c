#include <stdio.h> 
#include <stdlib.h> 
#include <fcntl.h>
#include <unistd.h>

#pragma code-name ("OVERLAY2");
#pragma rodata-name ("OVERLAY2");

int overlay2() { 
    printf("This is overaly 2.\n"); 
    return 1;
}
