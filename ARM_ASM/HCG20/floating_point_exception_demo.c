#include <stdio.h>
#include <signal.h>
#include <fenv.h>

#pragma STDC FENV_ACCESS ON
 
void floating_point_exception_handler(int signal) {
    printf("Floating-point exception caught!\n");
    feclearexcept(FE_ALL_EXCEPT);
}

int main() {
    // Enable floating-point exceptions
    int old_settings = 
	feenableexcept(
	    FE_INVALID 
	  | FE_DIVBYZERO 
	  | FE_OVERFLOW
	);

    // Clear the flags    
    feclearexcept(FE_ALL_EXCEPT); 

    // Install the signal handler
    signal(SIGFPE, floating_point_exception_handler);

    // Perform a division by zero to trigger an exception
    float x = 1.0f;
    float y = 0.0f;
    float result = x / y;

    printf("Result: %f\n", result);
    //feraiseexcept(FE_DIVBYZERO);
    return 0;
}

