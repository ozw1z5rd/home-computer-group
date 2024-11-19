
#include <stdio.h>
#include <cc65.h>
#include <cbm.h>
#include <device.h>
#include <peekpoke.h>
#include <conio.h>

extern void log(char *);
extern void wait_a_key(void);

#pragma code-name ("OVERLAY1");
#pragma rodata-name("OVERLAY1");

void foo (void)
{
    log("Calling log() from overlay 1");
    printf("This code has been loaded from disk\n");
    printf("and executed in the global context\n");
    wait_a_key();
}

