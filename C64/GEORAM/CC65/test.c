#include <stdio.h> 
#include <em.h> 
#include <conio.h>
// cp -f $(CC65_HOME)/target/c64/drv/emd/$(REU) $@

#define GEORAM "c64-georam.emd"

int main(void) { 
   printf("My program in C for the Commodore 64\n");


   // this will call init on the driver
   if ( em_load_driver(GEORAM) != 0) { 
       printf("Cannot load the georam driver!\n");
       printf("1) Driver not on disk\n"); 
       printf("2) Missing expansion\n");
       return 1;
   }

   printf("The number of pages is %d\n", em_pagecount() );
   return 0;  
}
