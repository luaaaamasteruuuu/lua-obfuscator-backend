import random

def encrypt_string(s,rng):
    plain=list(s.encode('utf-8'))
    keylen=rng.randint(4,max(4,len(plain)//2+1))
    key=[rng.randint(1,255) for _ in range(keylen)]
    cipher=[plain[i]^key[i%len(key)] for i in range(len(plain))]
    return cipher,key

class StringEncryptor:
    def __init__(self,seed=None):
        self.rng=random.Random(seed);self._cache={}
    def encrypt(self,s):
        if s not in self._cache:self._cache[s]=encrypt_string(s,self.rng)
        return self._cache[s]
    def inline_expr(self,s):
        cipher,key=self.encrypt(s)
        k_lit='{'+','.join(str(b) for b in key)+'}'
        c_lit='{'+','.join(str(b) for b in cipher)+'}'
        return(f'(function()local k={k_lit};local c={c_lit};local r={{}};'
            f'for i=1,#c do r[i]=string.char(bit32.bxor(c[i],k[((i-1)%#k)+1]))end;'
            f'return table.concat(r)end)()')
    def has(self,s):return s in self._cache