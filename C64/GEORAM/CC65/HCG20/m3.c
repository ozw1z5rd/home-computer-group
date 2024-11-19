
#include <stdio.h>
#include <cc65.h>
#include <cbm.h>
#include <device.h>

extern void log(char *);
extern void wait_a_key(void);

#pragma code-name ("OVERLAY3");
#pragma rodata-name ("OVERLAY3");

void foobar (void)
{
    log ("Calling main from overlay 3");
    printf("=====> Last overlay.\n");
    wait_a_key();    
}
