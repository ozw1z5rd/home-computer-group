/************************************** 
    Home Computer Group 2024
 
**************************************/
#include <stdio.h> 
#include <stdint.h>
#include <em.h> 
#include <c64.h>
#include <cbm.h>
#include <cc65.h> 
#include <unistd.h>
#include <stdlib.h> 
#include <conio.h> 
#include <stdbool.h>
#include <errno.h> 

#define GEORAM "c64-georam.emd"
// this structure is required to use the GeoRAM
struct em_copy emd;
uint16_t page = 0; 

extern void _OVERLAY2_LOAD__[], _OVERLAY2_SIZE__[];
extern void _OVERLAY1_LOAD__[], _OVERLAY1_SIZE__[];


extern int _curunit;
extern int overlay2();
extern int overlay1();

/*
void saveScreen() { 
    emd.buf = (void *)10;
    emd.offs = 0;
    emd.page = page;
    emd.count = 1000;
    em_copyto(&emd);

    page += 4;

    emd.buf = color_loc_pointer;
    emd.page = page;
    emd.offs = 0;
    emd.count = 1000;
    em_copyto(&emd);

    page += 4;
} 

void loadScreen() { 
    emd.buf = screen_loc_pointer;
    emd.offs = 0;
    emd.page = page; 
    emd.count = 1000;
    em_copyfrom(&emd);

    page += 4; 

    emd.buf = color_loc_pointer;
    emd.offs = 0;
    emd.page = page;
    emd.count = 1000;
    em_copyfrom(&emd);
 
    page += 4; 
} 
*/


bool loadOverlay(char *overlayName, void *startAddress, void *size) 
{ 
     static char filename[21];
     unsigned int r = 0; 
     sprintf(filename, "%s,p,r", overlayName);

     r = cbm_open(2, 8, 2, filename);
     if ( 0 == r ) 
     {
          r = cbm_read(2, startAddress, (unsigned)size);
          cbm_close(2); 
          if ( (unsigned)size == r ) 
          {
               printf("Read %s (%u bytes) from %d.", overlayName, r, 8);
          } 
          else 
          {
               printf("Error on %d reading %s, %d", 8, overlayName, _oserror);
          }
    }
    return 0 < r;
}

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


int main(void) {
    unsigned char exit_loop = 1;

    printf("CC65 Overlay demo.\n");
    printf("-----------------------------\n");
    printf(" Home Computer Group 2024\n\n");

    printf("Initializing the GeoRAM.");
    if ( init_GeoRAM() != 0 ) { 
        return 1;
    }

    do { 



    }  while ( ! exit_loop );

    if(loadOverlay("overlaytest.c64.1", 	&_OVERLAY1_LOAD__, &_OVERLAY1_SIZE__))
    {
	overlay1(); 
    }

    page = 0;
    return EXIT_SUCCESS;
}


