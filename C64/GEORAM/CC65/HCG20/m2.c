
#include <stdio.h>
#include <cc65.h>
#include <cbm.h>
#include <device.h>

extern void log(char *);
extern void wait_a_key(void);

#pragma code-name ("OVERLAY2");
#pragma rodata-name("OVERLAY2");

void bar (void)
{
    log ("Calling main from overlay 2");
    printf("Before being excuted, the code\n");
    printf("is buffered into the GeoRAM\n");
    wait_a_key();
}


