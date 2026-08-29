import random
from .isa import Op,Instr,Proto

def _rand_var(rng,n=6):
    return '__'+''.join(rng.choices('abcdefghijklmnopqrstuvwxyz',k=n))

def _split_blocks(code):
    leaders={0}
    for i,ins in enumerate(code):
        if ins.op in(Op.JMP,Op.JMP_TRUE,Op.JMP_FALSE,Op.LOOP):
            if ins.arg<len(code):leaders.add(ins.arg)
            if i+1<len(code):leaders.add(i+1)
        if ins.op==Op.RETURN:
            if i+1<len(code):leaders.add(i+1)
    leaders=sorted(leaders);blocks=[];starts=[]
    for idx,start in enumerate(leaders):
        end=leaders[idx+1] if idx+1<len(leaders) else len(code)
        blocks.append(code[start:end]);starts.append(start)
    return blocks,starts

def _inject_junk(proto,rng,count=3):
    for _ in range(count):
        pos=rng.randint(0,len(proto.code))
        for _ in range(rng.randint(1,4)):proto.code.insert(pos,Instr(Op.NOP))

def flatten_proto(proto,rng):
    for sub in proto.protos:flatten_proto(sub,rng)
    if len(proto.code)<4:return
    _inject_junk(proto,rng,count=rng.randint(2,5))
    blocks,starts=_split_blocks(proto.code);n=len(blocks)
    if n<2:return
    order=list(range(n));rng.shuffle(order)
    old_idx_to_block={}
    for bid,start in enumerate(starts):
        for i in range(start,starts[bid+1] if bid+1<len(starts) else len(proto.code)):
            old_idx_to_block[i]=bid
    new_code=[];block_new_start={}
    for bid in order:
        block_new_start[bid]=len(new_code)
        for ins in blocks[bid]:
            if ins.op in(Op.JMP,Op.JMP_TRUE,Op.JMP_FALSE,Op.LOOP):
                target_bid=old_idx_to_block.get(ins.arg,ins.arg)
                new_code.append(Instr(ins.op,target_bid,ins.arg2))
            else:new_code.append(Instr(ins.op,ins.arg,ins.arg2))
        last=blocks[bid][-1] if blocks[bid] else None
        next_bid=bid+1
        if last and last.op not in(Op.JMP,Op.RETURN) and next_bid<n:
            new_code.append(Instr(Op.JMP,next_bid))
    for ins in new_code:
        if ins.op in(Op.JMP,Op.JMP_TRUE,Op.JMP_FALSE,Op.LOOP):
            if ins.arg in block_new_start:ins.arg=block_new_start[ins.arg]
    proto.code=new_code

class Flattener:
    def __init__(self,seed=None):self.rng=random.Random(seed)
    def flatten(self,root_proto):flatten_proto(root_proto,self.rng);return root_proto