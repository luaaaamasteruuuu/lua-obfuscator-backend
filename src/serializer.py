import struct
from .isa import ISA,Proto

MAGIC=b'LUOB';VERSION=1

def _pack_u24(n):
    n=n&0xFFFFFF;return struct.pack('<I',n)[:3]

def _pack_const(v):
    if v is None:return b'\x00'
    if isinstance(v,bool):return bytes([0x01,0x01 if v else 0x00])
    if isinstance(v,int):return b'\x02'+struct.pack('<q',v)
    if isinstance(v,float):return b'\x03'+struct.pack('<d',v)
    if isinstance(v,str):enc=v.encode('utf-8');return b'\x04'+struct.pack('<H',len(enc))+enc
    raise TypeError(f"unsupported const {type(v)}")

def _serial_proto(proto,isa):
    out=bytearray()
    out+=bytes([proto.params,1 if proto.vararg else 0])
    out+=struct.pack('<H',len(proto.consts))
    for c in proto.consts:out+=_pack_const(c)
    out+=struct.pack('<H',len(proto.protos))
    for p in proto.protos:out+=_serial_proto(p,isa)
    out+=struct.pack('<I',len(proto.code))
    for ins in proto.code:out+=bytes([isa.byte(ins.op)])+_pack_u24(ins.arg)
    return bytes(out)

class Serializer:
    def __init__(self,isa,seed):self.isa=isa;self.seed=seed
    def serialize(self,root):
        body=_serial_proto(root,self.isa)
        header=MAGIC+bytes([VERSION])+struct.pack('<Q',self.seed&0xFFFFFFFFFFFFFFFF)
        return header+body
    def dump(self,root):return list(self.serialize(root))