
     .data

# the processor we are using does not allow
# to load the float in immediate addressing 
# mode. 
first_number:
    .float -3.0

second_numbers:
    .float -2.0


# Please note: there are two floating point
# numbers to be printed.
strfdouble:
    .asciz  "max(%f, %f) = %f\n"

    .text
    .align  2
    .global main

#
# MAIN()
#
main:
#
# Save the ARM registers supposed to be 
# used in this code 
#
    push {r0, r2, r3, lr}

# load the 1st number in s1 
# and the 2nd number in s2
    ldr r3, =first_number
    vldr.f32 s1, [r3] 
    #vsqrt.f32 s1, s1


    ldr r3, =second_numbers
    vldr.f32 s2, [r3] 
    #vsqrt.f32 s2, s2

# Compare the numbers and check if
# the result is a NaN, in this case
# at least a NaN is present
    vcmp.f32 s1, s2
    vmrs    APSR_nzcv, FPSCR
    # vs --> unordered
    bvs not_a_number

# No NaN detected, please note the
# conditional field used to select
# which vmov must be effective
    vmovge.f32 s0,s1
    vmovlt.f32 s0,s2

# exit the program 
    b print_result

not_a_number:

# at least a NaN, let's check s1
    vcmp.f32 s1, #0.0 
    vmrs APSR_nzcv, FPSCR
    # vc --> not unordered 
    vmovvc.f32 s0, s1
    vmovvs.f32 s0, s2

# The first float is passed via r2, r3
# the others are pushed into the 
# stack 

print_result:
# printf will not pop these values
    vcvt.f64.f32 d13, s0
    vmov r2, r3, d13
    push {r2, r3} 

    vcvt.f64.f32 d13, s2
    vmov r2, r3, d13
    push {r2, r3} 

    vcvt.f64.f32 d13, s1
    vmov r2, r3, d13 

    ldr r0, =strfdouble
    bl  printf

# so we have to remote them from 
# the stack by our own
    pop {r2, r3} 
    pop {r2, r3} 

# Restore the condition as of before 
# this routine
    pop {r0, r2, r3, lr}
    bx lr

