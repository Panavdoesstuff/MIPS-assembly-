.data
    result_msg: .asciiz "GCD = "
    newline:    .asciiz "\n"
.text
.globl main
main:
    addiu $sp, $sp, -8
    sw    $ra, 4($sp)
    sw    $s0, 0($sp)

    li    $a0, 48           # a = 48
    li    $a1, 32          # b = 18
    jal   gcd
    move  $s0, $v0          

    li    $v0, 4
    la    $a0, result_msg
    syscall

    li    $v0, 1
    move  $a0, $s0
    syscall

    li    $v0, 4
    la    $a0, newline
    syscall

    lw    $ra, 4($sp)
    lw    $s0, 0($sp)
    addiu $sp, $sp, 8

    li    $v0, 10
    syscall  
gcd:
gcd_loop:
    beq   $a1, $zero, gcd_done
    div   $a0, $a1          
    mfhi  $t0               
    move  $a0, $a1        
    move  $a1, $t0        
    j     gcd_loop
gcd_done:
    move  $v0, $a0
    jr    $ra
    
    