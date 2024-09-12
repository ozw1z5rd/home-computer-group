/************************************** 
 Home Computer Group 2024
 
**************************************/
#include <stdio.h> 
#include <stdint.h>
#include <em.h> 
#include <c64.h>
#include <cc65.h> 
#include <unistd.h>
#include <stdlib.h> 
#include <conio.h> 

#define GEORAM "c64-georam.emd"
// this structure is required to use the GeoRAM
struct em_copy emd;
uint16_t page = 0; 
char *screen_loc_pointer = (char *)1024;
char *color_loc_pointer = (char *)55296;


void saveScreen() { 
    emd.buf = screen_loc_pointer;
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
    int jj; 


    if ( init_GeoRAM() != 0 ) { 
    	return 1;
    }
    page = 0;
    saveScreen();
    printf("** Screen saved\n");
    sleep(5); 
    clrscr();
    
    for ( jj = 0; jj<= 40; jj++) {  
        printf("bla bla bla bla ");
    }
    
    saveScreen();
    printf("\n** Screen saved\n"); 
    sleep(5); 

    page = 0;
    loadScreen();
    printf("* SCREEN LOADED\n"); 
    sleep(5); 

    loadScreen(); 
    printf("** SCREEN LOADED\n");

    return EXIT_SUCCESS;
}
