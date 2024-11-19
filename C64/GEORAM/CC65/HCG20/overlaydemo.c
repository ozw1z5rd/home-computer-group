/*
** Minimalistic overlay demo program.
**
** Shows how to load overlay files from disk.
**
** 2009-10-02, Oliver Schmidt (ol.sc@web.de)
** 2024-11-15, Added support for GeoRAM ( fb.com/groups/home.computer )
**
*/

#include <stdio.h>
#include <cc65.h>
#include <cbm.h>
#include <device.h>
#include <em.h> 
#include <stdbool.h>
#include <errno.h> 
#include <unistd.h>
#include <c64.h>
#include <stdlib.h> 
#include <conio.h> 
#include <peekpoke.h>
#include <conio.h>

#define GEORAM "c64-georam.emd"
#define OVERLAY_SIZE 0x1000
#define OVERLAY_SIZE_IN_PAGES 0x10 

struct em_copy emd;

extern void foo(void);
extern void bar(void);
extern void foobar(void);

extern void _OVERLAY1_LOAD__[], _OVERLAY1_SIZE__[];
extern void _OVERLAY2_LOAD__[], _OVERLAY2_SIZE__[];
extern void _OVERLAY3_LOAD__[], _OVERLAY3_SIZE__[];

int buffers_status[10] = { 0,0,0,0,0,0,0,0,0,0 };
int i;

void log (char *msg)
{
    printf ("Log: %s\n", msg);
}

void wait_a_key(void) 
{
    POKE(53280,6);
    printf("\n press a key ... \n\n");
    cgetc();
    POKE(53280,14);

}
/* Initializes the GeoRAM expansion
*/
int init_GeoRAM(void) { 
   switch ( em_load_driver(GEORAM) ) { 
      case EM_ERR_NO_DRIVER:
          printf("No driver available\n");
          return 1;
      case EM_ERR_CANNOT_LOAD: 
          printf("Error loading the driver\n"); 
          return 1; 
      case EM_ERR_INV_DRIVER: 
          printf("Invalid driver\n"); 
          return 1; 
      case EM_ERR_NO_DEVICE: 
          printf("Hardware not found\n"); 
          return 1;
      case EM_ERR_INSTALLED:
          printf("Already installed\n"); 
          return 1;
   }
   return 0;
}

void buffer_overlay(void *addr, unsigned int slot) {
    emd.buf = addr;
    emd.offs = 0;
    emd.page = slot * OVERLAY_SIZE_IN_PAGES;
    emd.count = OVERLAY_SIZE;
    em_copyto(&emd);
} 

void recall_overlay(void *addr, unsigned int slot) { 
    emd.buf = addr;
    emd.offs = 0;
    emd.page = slot * OVERLAY_SIZE_IN_PAGES; 
    emd.count = OVERLAY_SIZE;
    em_copyfrom(&emd);
}

unsigned char loadfile (char *name, void *addr, void *size, int slot)
{
    /* Avoid compiler warnings about unused parameters. */
     (void) size;

    if ( buffers_status[slot] ) { 
        log("Loading from GeoRAM");
        POKE(53280,7);
        recall_overlay(addr, slot);
    } 
    else { 
        POKE(53280,2);
        if (cbm_load (name, getcurrentdevice (), NULL) == 0) {
            log("Loading overlay file failed");
            POKE(53280,14);
            return 0;
        }
        
        POKE(53280,4);
        log("Buffering to GeoRAM");
        buffer_overlay(addr, slot);
        buffers_status[slot] = 1;
    }
    POKE(53280,14);
    return 1;
}

int main (void)
{

    printf("CC65 Overlay demo.\n");
    printf("-----------------------------\n");
    printf("Home Computer Group 2024\n\n");

    log("Initializing the GeoRAM.");
    POKE(53280,3);
    if ( init_GeoRAM() != 0 ) { 
        return 1;
    }
    log("Done");

    for ( i = 0; i < 2; i++ ) {
        log ("Calling overlay 1 from main");
        if (loadfile ("ovrldemo.1", _OVERLAY1_LOAD__, _OVERLAY1_SIZE__, 0)) {
            foo ();
        }
        log ("Calling overlay 2 from main");
        if (loadfile ("ovrldemo.2", _OVERLAY2_LOAD__, _OVERLAY2_SIZE__, 1)) {
            bar ();
        }
        log ("Calling overlay 3 from main");
        if (loadfile ("ovrldemo.3", _OVERLAY3_LOAD__, _OVERLAY3_SIZE__, 2)) {
            foobar ();
        }
    }
    if (doesclrscrafterexit ()) {
        getchar ();
    }
}
