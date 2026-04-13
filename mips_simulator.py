import sys

def u32(v): return v & 0xFFFFFFFF
def s32(v): v = u32(v); return v - 0x100000000 if v >= 0x80000000 else v
def sext(v, b): return v - (1 << b) if v & (1 << (b-1)) else v

TEXT = 0x00400000
DATA = 0x10010000
SP0  = 0x7FFFFFFC

def fmt(v):
    """Hex for addresses/pointers, decimal for small data values."""
    u = u32(v)
    if u >= 0x00400000:
        return f"0x{u:08X}"
    return str(s32(v))

RNAMES = ["zero","at","v0","v1","a0","a1","a2","a3",
          "t0","t1","t2","t3","t4","t5","t6","t7",
          "s0","s1","s2","s3","s4","s5","s6","s7",
          "t8","t9","k0","k1","gp","sp","fp","ra"]

class RF:
    def __init__(self):
        self.r = [0]*32; self.r[28]=DATA+0x8000; self.r[29]=SP0
        self.HI = self.LO = 0
    def rd(self, i): return self.r[i]
    def wr(self, i, v):
        if i: self.r[i] = u32(v)

class Mem:
    def __init__(self): self.m = {}
    def lw(self, a): return self.m.get(a&~3, 0)
    def sw(self, a, v): self.m[a&~3] = u32(v)
    def lb(self, a):
        w=self.lw(a); sh=(a&3)*8; return (w>>sh)&0xFF
    def sb(self, a, v):
        w=self.lw(a); sh=(a&3)*8
        self.sw(a, (w & ~(0xFF<<sh)) | ((v&0xFF)<<sh))
    def str_at(self, a):
        s=""
        while True:
            b=self.lb(a)
            if not b: break
            s+=chr(b); a+=1
        return s
    def load_bin(self, path, base):
        i = 0
        with open(path) as f:
            for ln in f:
                ln = ln.strip()
                if not ln or ln.startswith("#") or ln.startswith("//"):
                    continue
                if ln.startswith("0x") or ln.startswith("0X"):
                    ln = ln[2:]
                ln = ln.replace(" ", "")
                if len(ln) != 32:
                    continue
                self.sw(base + i*4, int(ln, 2))
                i += 1

class CS:
    """All boolean control lines generated in ID stage."""
    def __init__(self):
        self.RegDst=self.ALUSrc=self.MemToReg=False
        self.RegWrite=self.MemRead=self.MemWrite=False
        self.Branch=self.BranchNE=self.Jump=self.JumpReg=self.Link=False
        self.BLEZ=self.BGTZ=self.BLTZ=self.BGEZ=False
        self.ZeroExt=self.Syscall=False
        self.ALUOp=0

def decode(op, fn, rt):
    cs=CS()
    if op in (0, 0x1C):
        cs.RegDst=True; cs.ALUOp=2
        if fn not in (0x18,0x19,0x1A,0x1B,0x11,0x13): cs.RegWrite=True
        if fn==0x0C: cs.RegWrite=False; cs.Syscall=True
        if fn==0x08: cs.JumpReg=True;  cs.RegWrite=False
        if fn==0x09: cs.JumpReg=True;  cs.Link=True
    elif op in (8,9):
        cs.ALUSrc=True; cs.RegWrite=True; cs.ALUOp=3
    elif op in (0xC,0xD,0xE):
        cs.ALUSrc=True; cs.RegWrite=True; cs.ZeroExt=True; cs.ALUOp=3
    elif op in (0xA,0xB):
        cs.ALUSrc=True; cs.RegWrite=True; cs.ALUOp=3
    elif op==0xF:
        cs.ALUSrc=True; cs.RegWrite=True; cs.ALUOp=3
    elif op in (0x23,0x20,0x24):
        cs.ALUSrc=True; cs.MemRead=True; cs.MemToReg=True; cs.RegWrite=True
    elif op in (0x2B,0x28):
        cs.ALUSrc=True; cs.MemWrite=True
    elif op==4:  cs.Branch=True; cs.ALUOp=1
    elif op==5:  cs.Branch=True; cs.BranchNE=True; cs.ALUOp=1
    elif op==6:  cs.Branch=True; cs.BLEZ=True; cs.ALUOp=1
    elif op==7:  cs.Branch=True; cs.BGTZ=True; cs.ALUOp=1
    elif op==1:
        cs.Branch=True; cs.ALUOp=1
        if   rt==0:  cs.BLTZ=True
        elif rt==1:  cs.BGEZ=True
        elif rt==16: cs.BLTZ=True; cs.Link=True; cs.RegWrite=True
        elif rt==17: cs.BGEZ=True; cs.Link=True; cs.RegWrite=True
    elif op==2: cs.Jump=True
    elif op==3: cs.Jump=True; cs.Link=True; cs.RegWrite=True
    return cs

def mnemonic(op, fn, rs, rt, rd, sh, imm_s, addr26):
    R = RNAMES
    if op == 0:
        fmap = {0x20:"add",0x21:"addu",0x22:"sub",0x23:"subu",
                0x24:"and",0x25:"or", 0x26:"xor",0x27:"nor",
                0x2A:"slt",0x2B:"sltu",0x18:"mult",0x19:"multu",
                0x1A:"div",0x1B:"divu",0x10:"mfhi",0x12:"mflo",
                0x11:"mthi",0x13:"mtlo",0x0C:"syscall",
                0x08:"jr",  0x09:"jalr"}
        m = fmap.get(fn, f"fn={fn:#04x}")
        if fn in (0x00,0x02,0x03):
            nm={0x00:"sll",0x02:"srl",0x03:"sra"}[fn]
            return f"{nm} ${R[rd]}, ${R[rt]}, {sh}"
        elif fn in (0x04,0x06,0x07):
            nm={0x04:"sllv",0x06:"srlv",0x07:"srav"}[fn]
            return f"{nm} ${R[rd]}, ${R[rt]}, ${R[rs]}"
        elif fn in (0x18,0x19,0x1A,0x1B):
            return f"{m} ${R[rs]}, ${R[rt]}"
        elif fn in (0x10,0x12): return f"{m} ${R[rd]}"
        elif fn in (0x11,0x13): return f"{m} ${R[rs]}"
        elif fn == 0x0C:        return "syscall"
        elif fn == 0x08:        return f"jr ${R[rs]}"
        elif fn == 0x09:        return f"jalr ${R[rd]}, ${R[rs]}"
        else:                   return f"{m} ${R[rd]}, ${R[rs]}, ${R[rt]}"
    elif op == 0x1C: return f"mul ${R[rd]}, ${R[rs]}, ${R[rt]}"
    elif op in (8,9):
        return f"{'addi' if op==8 else 'addiu'} ${R[rt]}, ${R[rs]}, {imm_s}"
    elif op == 0xC: return f"andi ${R[rt]}, ${R[rs]}, {imm_s}"
    elif op == 0xD: return f"ori  ${R[rt]}, ${R[rs]}, {imm_s}"
    elif op == 0xE: return f"xori ${R[rt]}, ${R[rs]}, {imm_s}"
    elif op in (0xA,0xB):
        return f"{'slti' if op==0xA else 'sltiu'} ${R[rt]}, ${R[rs]}, {imm_s}"
    elif op == 0xF:  return f"lui  ${R[rt]}, 0x{imm_s&0xFFFF:04X}"
    elif op == 0x23: return f"lw   ${R[rt]}, {imm_s}(${R[rs]})"
    elif op == 0x20: return f"lb   ${R[rt]}, {imm_s}(${R[rs]})"
    elif op == 0x24: return f"lbu  ${R[rt]}, {imm_s}(${R[rs]})"
    elif op == 0x2B: return f"sw   ${R[rt]}, {imm_s}(${R[rs]})"
    elif op == 0x28: return f"sb   ${R[rt]}, {imm_s}(${R[rs]})"
    elif op == 4:    return f"beq  ${R[rs]}, ${R[rt]}, {imm_s}"
    elif op == 5:    return f"bne  ${R[rs]}, ${R[rt]}, {imm_s}"
    elif op == 6:    return f"blez ${R[rs]}, {imm_s}"
    elif op == 7:    return f"bgtz ${R[rs]}, {imm_s}"
    elif op == 1:
        tags={0:"bltz",1:"bgez",16:"bltzal",17:"bgezal"}
        return f"{tags.get(rt,'regimm')} ${R[rs]}, {imm_s}"
    elif op == 2: return f"j    0x{addr26<<2:08X}"
    elif op == 3: return f"jal  0x{addr26<<2:08X}"
    return f"op=0x{op:02X}"

FUNCT = {
    0x20:"add",0x21:"addu",0x22:"sub",0x23:"subu",
    0x24:"and",0x25:"or",  0x26:"xor",0x27:"nor",
    0x2A:"slt",0x2B:"sltu",
    0x00:"sll",0x02:"srl",0x03:"sra",
    0x04:"sll",0x06:"srl",0x07:"sra",
    0x18:"mult",0x19:"multu",0x1A:"div",0x1B:"divu",
    0x10:"mfhi",0x12:"mflo",0x11:"mthi",0x13:"mtlo",
    0x08:"jr",  0x09:"jalr",
}
ITYPE_OP = {8:"add",9:"addu",0xC:"and",0xD:"or",0xE:"xor",0xA:"slt",0xB:"sltu",0xF:"lui"}

def alu_exec(op, aluop_ctrl, opcode, funct, A, B, shamt, HI, LO):
    if aluop_ctrl==0: op="add"
    elif aluop_ctrl==1: op="sub"
    elif aluop_ctrl==2:
        op = "mul" if opcode==0x1C else FUNCT.get(funct,"add")
    else:
        op = ITYPE_OP.get(opcode,"add")
    nHI,nLO=HI,LO
    As,Bs=s32(A),s32(B)
    Au,Bu=u32(A),u32(B)
    if   op=="add":   r=u32(As+Bs)
    elif op=="addu":  r=u32(As+Bs)
    elif op=="sub":   r=u32(As-Bs)
    elif op=="subu":  r=u32(As-Bs)
    elif op=="and":   r=Au&Bu
    elif op=="or":    r=Au|Bu
    elif op=="xor":   r=Au^Bu
    elif op=="nor":   r=u32(~(Au|Bu))
    elif op=="slt":   r=1 if As<Bs else 0
    elif op=="sltu":  r=1 if Au<Bu else 0
    elif op=="sll":   r=u32(Bu<<shamt)
    elif op=="srl":   r=(Bu>>shamt)&0xFFFFFFFF
    elif op=="sra":   r=u32(Bs>>shamt)
    elif op in ("mult","mul"):
        p=As*Bs; nHI=u32((p>>32)&0xFFFFFFFF); nLO=u32(p&0xFFFFFFFF); r=nLO
    elif op=="multu":
        p=Au*Bu; nHI=u32((p>>32)&0xFFFFFFFF); nLO=u32(p&0xFFFFFFFF); r=nLO
    elif op=="div":
        if Bs: nLO=u32(int(As/Bs)); nHI=u32(As-Bs*int(As/Bs))
        r=nLO
    elif op=="divu":
        if Bu: nLO=Au//Bu; nHI=Au%Bu
        r=nLO
    elif op=="mfhi": r=HI
    elif op=="mflo": r=LO
    elif op=="mthi": nHI=Au; r=0
    elif op=="mtlo": nLO=Au; r=0
    elif op=="lui":  r=u32(Bu<<16)
    else:            r=0
    r=u32(r)
    return r, r==0, nHI, nLO, op

SEP = "  " + "-"*56

class Processor:
    def __init__(self):
        self.rf=RF(); self.mem=Mem()
        self.pc=TEXT; self.alive=True; self.clk=0
        self._asm_lines=[]; self._asm_idx=0

    def load(self, text_path, data_path=None, asm_path=None):
        self.mem.load_bin(text_path, TEXT)
        if data_path: self.mem.load_bin(data_path, DATA)
        if asm_path:  self._load_asm(asm_path)

    def _load_asm(self, path):
        with open(path) as f:
            for ln in f:
                s = ln.strip()
                if s and not s.startswith('#'):
                    self._asm_lines.append(s)

    def _next_asm(self):
        while self._asm_idx < len(self._asm_lines):
            c = self._asm_lines[self._asm_idx]
            if c.startswith('.') or (
               ':' in c and ' ' not in c.split(':')[0].strip()
               and c.split(':')[0].strip().replace('_','').isalnum()):
                self._asm_idx += 1; continue
            self._asm_idx += 1
            return c
        return None

    def run(self, limit=500_000):
        print("MIPS32 Simulator  -  EG 212")
        print("="*60)

        while self.alive and self.clk < limit:
            self.clk += 1
            pc = self.pc
            instr = self.mem.lw(pc)
            if instr == 0 and self.clk > 1: break

            op=(instr>>26)&0x3F; rs=(instr>>21)&0x1F; rt=(instr>>16)&0x1F
            rd=(instr>>11)&0x1F; sh=(instr>>6)&0x1F;  fn=instr&0x3F
            imm=instr&0xFFFF; addr26=instr&0x3FFFFFF
            imm_s=sext(imm,16)
            is_rtype = op in (0, 0x1C)
            is_jtype = op in (2, 3)
            mn = mnemonic(op, fn, rs, rt, rd, sh, imm_s, addr26)

            # IF
            pc4 = pc+4; self.pc = pc4
            asm_src = self._next_asm() if self._asm_lines else None
            print(f"\n[Cycle {self.clk}]  PC=0x{pc:08X}")
            if asm_src:
                print(f"  IF   instr=0x{instr:08X}  >>  {mn}    [{asm_src}]")
            else:
                print(f"  IF   instr=0x{instr:08X}  >>  {mn}")

            # ID
            rsv=self.rf.rd(rs); rtv=self.rf.rd(rt)
            cs=decode(op,fn,rt)
            b = lambda v: int(bool(v))

            id_regs = f"$rs=${RNAMES[rs]}={fmt(rsv)}  $rt=${RNAMES[rt]}={fmt(rtv)}"
            if is_rtype:
                id_regs += f"  $rd=${RNAMES[rd]}"
                if fn in (0x00,0x02,0x03,0x04,0x06,0x07):
                    id_regs += f"  shamt={sh}"
            elif not is_jtype:
                id_regs += f"  imm={imm_s}"
            print(f"  ID   {id_regs}")
            print(f"       ctrl: RegWrite={b(cs.RegWrite)} ALUSrc={b(cs.ALUSrc)} "
                  f"MemRead={b(cs.MemRead)} MemWrite={b(cs.MemWrite)} "
                  f"Branch={b(cs.Branch)} Jump={b(cs.Jump)} "
                  f"RegDst={b(cs.RegDst)} MemToReg={b(cs.MemToReg)} ALUOp={cs.ALUOp}")

            # EX
            A=rsv
            B=(imm if cs.ZeroExt else u32(imm_s)) if cs.ALUSrc else rtv
            eff_sh = rsv&0x1F if fn in (4,6,7) else sh
            alu_r,zero,nHI,nLO,opname=alu_exec(None,cs.ALUOp,op,fn,A,B,eff_sh,self.rf.HI,self.rf.LO)
            self.rf.HI=nHI; self.rf.LO=nLO

            branch_t=u32(pc4+(imm_s<<2))
            jump_t=(pc4&0xF0000000)|(addr26<<2)
            rs_s=s32(rsv); take=False
            if cs.Branch:
                if   cs.BLEZ:     take=rs_s<=0
                elif cs.BGTZ:     take=rs_s>0
                elif cs.BLTZ:     take=rs_s<0
                elif cs.BGEZ:     take=rs_s>=0
                elif cs.BranchNE: take=not zero
                else:             take=zero
            if   cs.JumpReg: self.pc=rsv
            elif cs.Jump:    self.pc=jump_t
            elif take:       self.pc=branch_t

            if cs.Jump and cs.Link:       wreg=31
            elif cs.Link and cs.JumpReg:  wreg=rd
            elif cs.RegDst:               wreg=rd
            else:                         wreg=rt

            if cs.JumpReg:
                print(f"  EX   jr -> 0x{rsv:08X}   nextPC=0x{self.pc:08X}")
            elif cs.Jump:
                print(f"  EX   jump -> 0x{self.pc:08X}")
            elif cs.Branch:
                btype=("blez" if cs.BLEZ else "bgtz" if cs.BGTZ else
                       "bltz" if cs.BLTZ else "bgez" if cs.BGEZ else
                       "bne"  if cs.BranchNE else "beq")
                print(f"  EX   {btype}  target=0x{branch_t:08X}  taken={take}   nextPC=0x{self.pc:08X}")
            elif opname in ("sll","srl","sra"):
                print(f"  EX   {opname}  {fmt(B)} >> {eff_sh}  =  {fmt(alu_r)}   nextPC=0x{self.pc:08X}")
            elif opname in ("mult","multu","div","divu"):
                print(f"  EX   {opname}({fmt(A)}, {fmt(B)})  -> HI={fmt(nHI)}  LO={fmt(nLO)}   nextPC=0x{self.pc:08X}")
            elif opname in ("mfhi","mflo","mthi","mtlo"):
                print(f"  EX   {opname}  ->  {fmt(alu_r)}   nextPC=0x{self.pc:08X}")
            else:
                print(f"  EX   {opname}({fmt(A)}, {fmt(B)})  =  {fmt(alu_r)}   nextPC=0x{self.pc:08X}")

            # MEM
            mem_d=0
            if cs.MemRead:
                if op==0x24: mem_d=self.mem.lb(alu_r)
                elif op==0x20: mem_d=u32(sext(self.mem.lb(alu_r),8))
                else:          mem_d=self.mem.lw(alu_r)
                print(f"  MEM  load   MEM[0x{alu_r:08X}]  ->  {fmt(mem_d)}")
            elif cs.MemWrite:
                if op==0x28: self.mem.sb(alu_r,rtv)
                else:        self.mem.sw(alu_r,rtv)
                print(f"  MEM  store  {fmt(rtv)}  ->  MEM[0x{alu_r:08X}]")
            else:
                print(f"  MEM  -")

            # WB
            if cs.Syscall:
                self._syscall()
                print(f"  WB   syscall")
            elif cs.RegWrite:
                if cs.Link:
                    self.rf.wr(wreg,pc4)
                    print(f"  WB   ${RNAMES[wreg]}  <-  0x{pc4:08X}  (return address)")
                elif opname in ("mult","multu","div","divu","mthi","mtlo"):
                    print(f"  WB   HI={fmt(self.rf.HI)}  LO={fmt(self.rf.LO)}")
                elif cs.MemToReg:
                    self.rf.wr(wreg,mem_d)
                    print(f"  WB   ${RNAMES[wreg]}  <-  {fmt(mem_d)}")
                else:
                    self.rf.wr(wreg,alu_r)
                    print(f"  WB   ${RNAMES[wreg]}  <-  {fmt(alu_r)}")
            else:
                print(f"  WB   -")

            print(SEP)

        print(f"\n{'='*60}\nDone in {self.clk} cycles.")

    def _syscall(self):
        svc=s32(self.rf.rd(2)); a0=self.rf.rd(4)
        if   svc==1:  print(f"\n  [OUTPUT] {s32(a0)}")
        elif svc==4:  print(f"\n  [OUTPUT] {self.mem.str_at(a0)}")
        elif svc==5:  self.rf.wr(2, int(input("  [INPUT]  ")))
        elif svc==10: self.alive=False; print("  [OUTPUT] exit")
        elif svc==11: print(f"\n  [OUTPUT] {chr(a0&0xFF)}")
        else:         print(f"  [OUTPUT] syscall {svc} ignored")


if __name__=="__main__":
    import argparse
    parser = argparse.ArgumentParser(description="MIPS32 Simulator - EG 212")
    parser.add_argument("instr", help="Binary text dump of .text segment (MARS)")
    parser.add_argument("var",   nargs="?", help="Binary text dump of .data segment (MARS)")
    parser.add_argument("--asm", help="Original .asm source (shown inline in IF stage)")
    args = parser.parse_args()
    p = Processor()
    p.load(args.instr, args.var, args.asm)
    p.run()