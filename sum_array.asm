.data
    array:      .word 3, 7, 2, 9, 11
    n:          .word 5
    msg_sum:    .asciiz "Sum = "
    newline:    .asciiz "\n"

.text
.globl main

main:

    addiu   $sp, $sp, -8
    sw      $ra, 4($sp)
    sw      $s0, 0($sp)


    la      $a0, array         
    lw      $a1, n              

    jal     sumArray
    move    $s0, $v0            

    la      $a0, msg_sum
    li      $v0, 4
    syscall

    move    $a0, $s0
    li      $v0, 1
    syscall

    la      $a0, newline
    li      $v0, 4
    syscall

    lw      $ra, 4($sp)
    lw      $s0, 0($sp)
    addiu   $sp, $sp, 8
    li      $v0, 10
    syscall

sumArray:
    addiu   $sp, $sp, -8
    sw      $ra, 4($sp)
    sw      $s0, 0($sp)

    move    $s0, $a0            
    li      $v0, 0             
    li      $t0, 0           

loop:
    beq     $t0, $a1, done      

    sll     $t1, $t0, 2        
    add     $t1, $s0, $t1       
    lw      $t2, 0($t1)        
    add     $v0, $v0, $t2      

    addiu   $t0, $t0, 1        
    j       loop

done:
    lw      $ra, 4($sp)
    lw      $s0, 0($sp)
    addiu   $sp, $sp, 8
    jr      $ra