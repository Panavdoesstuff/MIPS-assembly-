        .data
mat:    .word 1, 1, 1, 0        
res:    .word 1, 0, 0, 1       
temp:   .word 0, 0, 0, 0        
result_msg: .asciiz "Final Result (res[0]): "
newline:    .asciiz "\n"
        .text
        .globl main
main:
        addiu   $sp, $sp, -8
        sw      $ra,  4($sp)
        sw      $s0,  0($sp)
        la      $a0, mat
        li      $a1, 19                
        li      $a2, 14          
        jal     power                  
        move    $s0, $v0                
        la      $a0, result_msg
        li      $v0, 4                  
        syscall
        move    $a0, $s0
        li      $v0, 1                  
        syscall
        la      $a0, newline
        li      $v0, 4
        syscall
        lw      $ra,  4($sp)
        lw      $s0,  0($sp)
        addiu   $sp, $sp,  8
        li      $v0, 10                
        syscall
power:
        addiu   $sp, $sp, -28
        sw      $ra,  24($sp)
        sw      $s0,  20($sp)           # s0 = mat address
        sw      $s1,  16($sp)           # s1 = n
        sw      $s2,  12($sp)           # s2 = m
        sw      $s3,   8($sp)           # s3 = &res
        sw      $s4,   4($sp)           # s4 = &temp
        sw      $s5,   0($sp)

        move    $s0, $a0
        move    $s1, $a1
        move    $s2, $a2

        addiu   $s1, $s1, -1            
        la      $s3, res
        li      $t0, 1
        sw      $t0,  0($s3)            # res[0] = 1
        sw      $zero, 4($s3)           # res[1] = 0
        sw      $zero, 8($s3)           # res[2] = 0
        sw      $t0, 12($s3)            # res[3] = 1

        la      $s4, temp
power_loop:
        blez    $s1, power_done
        andi    $t0, $s1, 1
        beq     $t0, $zero, power_even
        move    $a0, $s3                # A = res
        move    $a1, $s0                # B = mat
        move    $a2, $s4                # output = temp
        move    $a3, $s2                # m
        jal     MM

        move    $a0, $s3                # dest = res
        move    $a1, $s4                # src  = temp
        jal     copy_matrix             # res = temp

power_even:
        move    $a0, $s0
        move    $a1, $s0
        move    $a2, $s4
        move    $a3, $s2
        jal     MM

        move    $a0, $s0
        move    $a1, $s4
        jal     copy_matrix

        srl     $s1, $s1, 1             # n = n / 2
        j       power_loop

power_done:
        lw      $v0,  0($s3)            # return res[0]

        lw      $ra,  24($sp)
        lw      $s0,  20($sp)
        lw      $s1,  16($sp)
        lw      $s2,  12($sp)
        lw      $s3,   8($sp)
        lw      $s4,   4($sp)
        lw      $s5,   0($sp)
        addiu   $sp, $sp, 28
        jr      $ra

MM:
        addiu   $sp, $sp, -24
        sw      $ra,  20($sp)
        sw      $s0,  16($sp)           # s0 = &A
        sw      $s1,  12($sp)           # s1 = &B
        sw      $s2,   8($sp)           # s2 = &result
        sw      $s3,   4($sp)           # s3 = m
        sw      $s4,   0($sp)

        move    $s0, $a0
        move    $s1, $a1
        move    $s2, $a2
        move    $s3, $a3

        # result[0] = (A[0]*B[0] + A[1]*B[2]) % m
        lw      $t0,  0($s0)            # A[0]  offset 0
        lw      $t1,  0($s1)            # B[0]  offset 0
        mul     $t0, $t0, $t1
        lw      $t2,  4($s0)            # A[1]  offset 4
        lw      $t3,  8($s1)            # B[2]  offset 8
        mul     $t2, $t2, $t3
        add     $t0, $t0, $t2
        div     $t0, $s3
        mfhi    $t0                     # t0 = sum % m
        sw      $t0,  0($s2)            # result[0]

        # result[1] = (A[0]*B[1] + A[1]*B[3]) % m
        lw      $t0,  0($s0)            # A[0]  offset 0
        lw      $t1,  4($s1)            # B[1]  offset 4
        mul     $t0, $t0, $t1
        lw      $t2,  4($s0)            # A[1]  offset 4
        lw      $t3, 12($s1)            # B[3]  offset 12
        mul     $t2, $t2, $t3
        add     $t0, $t0, $t2
        div     $t0, $s3
        mfhi    $t0
        sw      $t0,  4($s2)            # result[1]

        # result[2] = (A[2]*B[0] + A[3]*B[2]) % m
        lw      $t0,  8($s0)            # A[2]  offset 8
        lw      $t1,  0($s1)            # B[0]  offset 0
        mul     $t0, $t0, $t1
        lw      $t2, 12($s0)            # A[3]  offset 12
        lw      $t3,  8($s1)            # B[2]  offset 8
        mul     $t2, $t2, $t3
        add     $t0, $t0, $t2
        div     $t0, $s3
        mfhi    $t0
        sw      $t0,  8($s2)            # result[2]

        # result[3] = (A[2]*B[1] + A[3]*B[3]) % m
        lw      $t0,  8($s0)            # A[2]  offset 8
        lw      $t1,  4($s1)            # B[1]  offset 4
        mul     $t0, $t0, $t1
        lw      $t2, 12($s0)            # A[3]  offset 12
        lw      $t3, 12($s1)            # B[3]  offset 12
        mul     $t2, $t2, $t3
        add     $t0, $t0, $t2
        div     $t0, $s3
        mfhi    $t0
        sw      $t0, 12($s2)            # result[3]

        lw      $ra,  20($sp)
        lw      $s0,  16($sp)
        lw      $s1,  12($sp)
        lw      $s2,   8($sp)
        lw      $s3,   4($sp)
        lw      $s4,   0($sp)
        addiu   $sp, $sp, 24
        jr      $ra
copy_matrix:
        lw      $t0,  0($a1)
        sw      $t0,  0($a0)
        lw      $t0,  4($a1)
        sw      $t0,  4($a0)
        lw      $t0,  8($a1)
        sw      $t0,  8($a0)
        lw      $t0, 12($a1)
        sw      $t0, 12($a0)
        jr      $ra