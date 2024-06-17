
     .data

# the processor we are using does not allow
# to load the float in immediate addressing 
# mode. 
one:
    .float 1.0

# Please note: there are two floating point
# numbers to be printed.
strfdouble:
    .asciz  "cos(%f)=%f\n"

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


# This code will load 1.0 into the register s1 
# which is the accumulator for the factorial
# it saves the 1.0 into the s10 for later use

    # let f=1
    ldr r3, =one
    vldr.f32 s1, [r3]
    vmov.f32 s10, s1

    # let x = 1.0
    vmov.f32 s0, s10

    # let cx = 1
    vmov.f32 s2, s10

    # let s = -1 
    vmov.f32 s3, s10
    vneg.f32 s3, s3

# This is the beginning of the FOR cycle 
# structures as a do while
    mov r3, #1

loop: 
    # do 

    # let x = x * x
    vmul.f32 s0, s0, s0

    # let f = f * (2*k)*(2*k-1)               
    vmov s4, r3
    vcvt.f32.u32 s4, s4
    vadd.f32 s4, s4, s4 
    vmul.f32 s1, s1, s4
    vsub.f32 s4, s4, s10
    vmul.f32 s1, s1, s4 

    # let cx = cx + s * x / f 
    vmul.f32 s11, s3, s0
    vdiv.f32 s11, s11, s1
    vadd.f32 s2, s2, s11

    # let s = - s
    vneg.f32 s3,s3

    # while k < 5 
    add r3,r3, #1
    cmp r3, #5
    blt loop

    # s2 -> the result 
    # s0 -> the x 

# The first float is passed via r2, r3
# the second float is pushed into the 
# stack 
    vcvt.f64.f32 d13, s2
    vmov r2, r3, d13
# printf will not pop these values
    push {r2, r3} 

    vcvt.f64.f32 d13, s0
    vmov r2, r3, d13 

    ldr r0, =strfdouble
    bl  printf
# so we have to remote them from 
# the stack by our own
    pop {r2, r3} 

# Restore the condition as of before 
# this routine
    pop {r0, r2, r3, lr}
    bx lr

