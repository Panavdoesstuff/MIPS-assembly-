# Assignment 2: MIPS Processor Design & Assembly
**Course:** EGC 121 - Computer Architecture  

---

## Team Members
- Panav RG — BC2025069
- Ananya Singh — BC2025009
- Karthik Annadurai — IMT2025016

---

## Files

| File | Description |
|------|-------------|
| `matrix_power.asm` | MIPS assembly — Matrix Exponentiation (Fibonacci mod m) |
| `sum_array.asm` | MIPS assembly — Sum of elements in an array |
| `gcd.asm` | MIPS assembly — GCD using Euclidean algorithm |
| `text.txt` | Machine code binary dump of .text segment (MARS output) |
| `var.txt` | Data segment binary dump (MARS output) |
| `mips_simulator.py` | Non-pipelined MIPS32 processor simulator |
| `Report.pdf` | Project report with design details and results |

---

## Assembly Programs

### 1. Matrix Exponentiation (`matrix_power.asm`) - Panav RG
Computes Fibonacci(n) mod m using fast binary matrix exponentiation.  
The matrix `[[1,1],[1,0]]` is raised to power n, mod m.  
**Input:** n=19, m=14 — **Output:** `Final Result (res[0]): 9`

### 2. Sum Array (`sum_array.asm`) - Ananya Singh
Iterates over an array of n integers and computes their sum using a loop with indexed memory access.  
**Input:** `{3, 7, 2, 9, 11}`, n=5 — **Output:** `Sum = 32`

### 3. GCD (`gcd.asm`) - Karthik Annadurai
Computes the Greatest Common Divisor of two integers using the iterative Euclidean algorithm (repeated division and remainder).  
**Input:** a=48, b=32 — **Output:** `GCD = 16`

---

## Instructions Used (across all programs)

| Category | Instructions |
|----------|-------------|
| Memory | `LW`, `SW` |
| Control Flow | `JAL`, `JR`, `J`, `BEQ`, `BLEZ` |
| Arithmetic | `ADDIU`, `ADD`, `MUL`, `DIV`, `MFHI`, `SLL`, `SRL` |
| Logical | `ANDI`, `ORI`, `LUI` |
| Syscall | `SYSCALL` (print int, print string, exit) |

---

## How to Run the Simulator

```bash
python3 mips_simulator.py text.txt var.txt --asm matrix_power.asm
```

- `text.txt` — instruction memory (binary, one 32-bit word per line)
- `var.txt` — data memory (binary, one 32-bit word per line)
- `--asm` — optional, shows original assembly source inline during simulation


## Simulator Details
Executes machine code through a 5-stage non-pipelined MIPS processor, printing a full trace for every instruction:
```
[Cycle 1]  PC=0x00400000
  IF   instr=0x27BDFFF8  >>  addiu $sp, $sp, -8
  ID   $rs=$sp=0x7FFFFFFC  $rt=$sp=0x7FFFFFFC  imm=-8
       ctrl: RegWrite=1 ALUSrc=1 MemRead=0 MemWrite=0 Branch=0 Jump=0 ...
  EX   addu(0x7FFFFFFC, 0xFFFFFFF8)  =  0x7FFFFFF4   nextPC=0x00400004
  MEM  -
  WB   $sp  <-  0x7FFFFFF4
```

**Control signals (bool):** `RegWrite`, `ALUSrc`, `MemRead`, `MemWrite`, `MemToReg`, `RegDst`, `Branch`, `Jump`, `Link`, `JumpReg`  