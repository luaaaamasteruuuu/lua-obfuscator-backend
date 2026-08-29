import random
from enum import Enum,auto

class Op(Enum):
    PUSH_NIL=auto();PUSH_TRUE=auto();PUSH_FALSE=auto()
    PUSH_NUMBER=auto();PUSH_STRING=auto();PUSH_LOCAL=auto()
    PUSH_GLOBAL=auto();PUSH_UPVAL=auto();PUSH_VARARG=auto()
    PUSH_TABLE=auto();PUSH_CLOSURE=auto()
    SET_LOCAL=auto();SET_GLOBAL=auto();SET_UPVAL=auto()
    SET_TABLE=auto();GET_TABLE=auto();SET_FIELD=auto()
    GET_FIELD=auto();NEW_TABLE=auto()
    ADD=auto();SUB=auto();MUL=auto();DIV=auto()
    MOD=auto();POW=auto();IDIV=auto()
    BAND=auto();BOR=auto();BXOR=auto()
    SHL=auto();SHR=auto();BNOT=auto()
    UNM=auto();LEN=auto();NOT=auto();CONCAT=auto()
    EQ=auto();NEQ=auto();LT=auto();LE=auto();GT=auto();GE=auto()
    JMP=auto();JMP_TRUE=auto();JMP_FALSE=auto();LOOP=auto();RETURN=auto()
    CALL=auto();CALL_MULTI=auto();METHOD=auto()
    POP=auto();DUP=auto();SWAP=auto();NOP=auto()

class ISA:
    def __init__(self,seed=None):
        ops=list(Op)
        rng=random.Random(seed)
        nums=rng.sample(range(0,256),len(ops))
        self.encode={op:nums[i] for i,op in enumerate(ops)}
        self.decode={v:k for k,v in self.encode.items()}
    def byte(self,op):return self.encode[op]
    def op(self,byte):return self.decode[byte]

class Instr:
    __slots__=('op','arg','arg2')
    def __init__(self,op,arg=0,arg2=0):
        self.op=op;self.arg=arg;self.arg2=arg2

class Proto:
    def __init__(self):
        self.code=[];self.consts=[];self.protos=[]
        self.upvals=[];self.locals=[];self.params=0;self.vararg=False
    def add_const(self,v):
        if v in self.consts:return self.consts.index(v)
        self.consts.append(v);return len(self.consts)-1
    def add_proto(self,p):
        self.protos.append(p);return len(self.protos)-1
    def emit(self,op,arg=0,arg2=0):
        self.code.append(Instr(op,arg,arg2));return len(self.code)-1
    def patch(self,idx,arg):self.code[idx].arg=arg