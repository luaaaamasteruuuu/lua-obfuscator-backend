import random

_ROBLOX_GLOBALS=['game','workspace','script','Instance','Vector3','CFrame','Color3','UDim2']
_EXECUTOR_SIGS=['is_executor_closure','getgenv','getsenv','getrawmetatable','hookfunction','newcclosure','syn','KRNL_LOADED','saveinstance','readfile','writefile']

def _rv(rng):return '_'+''.join(rng.choices('abcdefghijklmnopqrstuvwxyz',k=6))

def generate_env_check(rng=None):
    if rng is None:rng=random.Random()
    v_ok=_rv(rng);v_flag=_rv(rng);lines=[]
    lines.append(f"local {v_ok}=true")
    for g in rng.sample(_ROBLOX_GLOBALS,min(4,len(_ROBLOX_GLOBALS))):
        lines.append(f"if type({g})~='userdata' and type({g})~='table' then {v_ok}=false end")
    lines.append(f"if not {v_ok} then return end")
    lines.append(f"local {v_flag}=false")
    for sig in rng.sample(_EXECUTOR_SIGS,min(5,len(_EXECUTOR_SIGS))):
        lines.append(f"if {sig}~=nil then {v_flag}=true end")
    lines.append(f"if {v_flag} then return end")
    return '\n'.join(lines)

def _rolling_hash(blob):
    h=0
    for b in blob:h=(h*31+b)%1000003
    return h

def generate_integrity_check(blob,rng=None):
    if rng is None:rng=random.Random()
    expected=_rolling_hash(blob);v_hash=_rv(rng);v_acc=_rv(rng);v_i=_rv(rng)
    p=rng.randint(100,999);q=p*p-expected
    lines=[f"local {v_hash}=0",f"for {v_i}=1,#__b do {v_hash}=({v_hash}*31+__b[{v_i}])%1000003 end",
        f"local {v_acc}={p}*{p}-({q})",f"if {v_hash}~={v_acc} then return end"]
    return '\n'.join(lines)

def generate_anti_debug(rng=None):
    if rng is None:rng=random.Random()
    v_t0=_rv(rng);v_t1=_rv(rng);v_d=_rv(rng)
    threshold=round(rng.uniform(0.4,0.8),2);iters=rng.randint(800,1200)
    lines=[f"local {v_t0}=os and os.clock and os.clock() or 0",
        f"local {v_d}=0",f"for _=1,{iters} do {v_d}={v_d}+1 end",
        f"local {v_t1}=os and os.clock and os.clock() or 0",
        f"if ({v_t1}-{v_t0})>{threshold} then return end"]
    return '\n'.join(lines)