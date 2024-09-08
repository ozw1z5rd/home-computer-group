#include <fenv.h>
#include <stdio.h>
#include <math.h>

int main() {
    // Clear all floating-point exceptions
    feclearexcept(FE_ALL_EXCEPT);

    // Perform a floating-point operation that may raise an exception
    double result = 1.0 / 0.0; // This will raise a division by zero exception

    // Check if the division by zero exception was raised
    if (fetestexcept(FE_DIVBYZERO)) {
        printf("Division by zero exception occurred.\n");
    }

    // Clear the division by zero exception
    feclearexcept(FE_DIVBYZERO);

    return 0;
}
