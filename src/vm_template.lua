local _vm_run
do
  local function _read_u8(blob,pos) return blob[pos],pos+1 end
  local function _read_u16(blob,pos) return blob[pos]+blob[pos+1]*256,pos+2 end
  local function _read_u24(blob,pos) return blob[pos]+blob[pos+1]*256+blob[pos+2]*65536,pos+3 end
  local function _read_u32(blob,pos) return blob[pos]+blob[pos+1]*256+blob[pos+2]*65536+blob[pos+3]*16777216,pos+4 end
  local function _read_f64(blob,pos)
    local ok,val=pcall(function()
      local bytes=string.char(table.unpack(blob,pos,pos+7))
      return string.unpack('<d',bytes)
    end)
    return ok and val or 0,pos+8
  end
  local function _read_str(blob,pos)
    local len,p=_read_u16(blob,pos);local chars={}
    for i=1,len do chars[i]=string.char(blob[p+i-1]) end
    return table.concat(chars),p+len
  end
  local function _deserialize(blob,pos)
    local params,p=_read_u8(blob,pos)
    local vararg,p=_read_u8(blob,p)
    local n_consts,p=_read_u16(blob,p)
    local consts={}
    for i=1,n_consts do
      local ctype,p2=_read_u8(blob,p)
      if ctype==0 then consts[i]=nil;p=p2
      elseif ctype==1 then local v;v,p=_read_u8(blob,p2);consts[i]=(v==1)
      elseif ctype==2 then local lo,p3=_read_u32(blob,p2);consts[i]=lo;p=p3+4
      elseif ctype==3 then consts[i],p=_read_f64(blob,p2)
      elseif ctype==4 then consts[i],p=_read_str(blob,p2)
      end
    end
    local n_protos,p=_read_u16(blob,p);local protos={}
    for i=1,n_protos do protos[i],p=_deserialize(blob,p) end
    local n_code,p=_read_u32(blob,p);local code={}
    for i=1,n_code do
      local op,p2=_read_u8(blob,p);local arg,p3=_read_u24(blob,p2)
      code[i]={op,arg};p=p3
    end
    return{params=params,vararg=vararg==1,consts=consts,protos=protos,code=code},p
  end
  local function _exec(proto,isa,upvals,args)
    local stack={};local sp=0;local locals={}
    for i,v in ipairs(args or{})do locals[i-1]=v end
    local function push(v)sp=sp+1;stack[sp]=v end
    local function pop()local v=stack[sp];sp=sp-1;return v end
    local function peek()return stack[sp]end
    local pc=1
    while pc<=#proto.code do
      local ins=proto.code[pc];local byte=ins[1];local arg=ins[2]
      local opname=isa[byte];pc=pc+1
      if opname=='PUSH_NIL' then push(nil)
      elseif opname=='PUSH_TRUE' then push(true)
      elseif opname=='PUSH_FALSE' then push(false)
      elseif opname=='PUSH_NUMBER' then push(proto.consts[arg+1])
      elseif opname=='PUSH_STRING' then push(proto.consts[arg+1])
      elseif opname=='PUSH_LOCAL' then push(locals[arg])
      elseif opname=='PUSH_GLOBAL' then local n=proto.consts[arg+1];push(_G and _G[n] or nil)
      elseif opname=='PUSH_UPVAL' then push(upvals and upvals[arg+1])
      elseif opname=='PUSH_VARARG' then push(args and args[proto.params+1] or nil)
      elseif opname=='SET_LOCAL' then locals[arg]=pop()
      elseif opname=='SET_GLOBAL' then local n=proto.consts[arg+1];if _G then _G[n]=pop() end
      elseif opname=='GET_TABLE' then local k=pop();local t=pop();push(t and t[k] or nil)
      elseif opname=='SET_TABLE' then local v=pop();local k=pop();local t=pop();if t then t[k]=v end
      elseif opname=='GET_FIELD' then local t=pop();push(t and t[proto.consts[arg+1]] or nil)
      elseif opname=='SET_FIELD' then local v=pop();local t=pop();if t then t[proto.consts[arg+1]]=v end
      elseif opname=='NEW_TABLE' then push({})
      elseif opname=='ADD' then local b=pop();push(pop()+b)
      elseif opname=='SUB' then local b=pop();push(pop()-b)
      elseif opname=='MUL' then local b=pop();push(pop()*b)
      elseif opname=='DIV' then local b=pop();push(pop()/b)
      elseif opname=='MOD' then local b=pop();push(pop()%b)
      elseif opname=='POW' then local b=pop();push(pop()^b)
      elseif opname=='IDIV' then local b=pop();push(math.floor(pop()/b))
      elseif opname=='UNM' then push(-pop())
      elseif opname=='NOT' then push(not pop())
      elseif opname=='LEN' then push(#pop())
      elseif opname=='CONCAT' then local b=tostring(pop());push(tostring(pop())..b)
      elseif opname=='BAND' then local b=pop();push(bit32.band(pop(),b))
      elseif opname=='BOR' then local b=pop();push(bit32.bor(pop(),b))
      elseif opname=='BXOR' then local b=pop();push(bit32.bxor(pop(),b))
      elseif opname=='SHL' then local b=pop();push(bit32.lshift(pop(),b))
      elseif opname=='SHR' then local b=pop();push(bit32.rshift(pop(),b))
      elseif opname=='BNOT' then push(bit32.bnot(pop()))
      elseif opname=='EQ' then local b=pop();push(pop()==b)
      elseif opname=='NEQ' then local b=pop();push(pop()~=b)
      elseif opname=='LT' then local b=pop();push(pop()<b)
      elseif opname=='LE' then local b=pop();push(pop()<=b)
      elseif opname=='GT' then local b=pop();push(pop()>b)
      elseif opname=='GE' then local b=pop();push(pop()>=b)
      elseif opname=='JMP' then pc=arg+1
      elseif opname=='JMP_TRUE' then if pop() then pc=arg+1 end
      elseif opname=='JMP_FALSE' then if not pop() then pc=arg+1 end
      elseif opname=='LOOP' then
        local ctr=pop();local lim=pop();local stp=pop();ctr=ctr+stp
        if(stp>=0 and ctr>lim)or(stp<0 and ctr<lim)then pc=arg+1
        else push(stp);push(lim);push(ctr);push(ctr)end
      elseif opname=='CALL' then
        local nargs=arg;local a={}
        for i=nargs,1,-1 do a[i]=pop()end;local fn=pop()
        if type(fn)=='function' then push(fn(table.unpack(a)))end
      elseif opname=='CALL_MULTI' then
        local niter=ins[2];local nres=ins[3] or 1;local iters={}
        for i=niter,1,-1 do iters[i]=pop()end
        local results={iters[1](table.unpack(iters,2))}
        for i=nres,1,-1 do push(results[i])end;push(results[1])
      elseif opname=='METHOD' then
        local mname=proto.consts[arg+1];local nargs=ins[3] or 0;local a={}
        for i=nargs,1,-1 do a[i]=pop()end;local obj=pop()
        if obj and obj[mname] then push(obj[mname](obj,table.unpack(a)))end
      elseif opname=='PUSH_CLOSURE' then
        local sub=proto.protos[arg+1]
        push(function(...)return _exec(sub,isa,upvals,{...})end)
      elseif opname=='RETURN' then
        local n=arg;local ret={}
        for i=n,1,-1 do ret[i]=pop()end;return table.unpack(ret)
      elseif opname=='DUP' then push(peek())
      elseif opname=='SWAP' then local a=pop();local b=pop();push(a);push(b)
      elseif opname=='POP' then pop()
      end
    end
  end
  local function _resolve_strings(proto,S)
    if not S then return end
    for i,c in ipairs(proto.consts)do
      if type(c)=='string' and c:sub(1,1)=='\0' then
        local idx=tonumber(c:match('\0ENC:(%d+)'))
        if idx and S[idx] then proto.consts[i]=S[idx]()end
      end
    end
    for _,sub in ipairs(proto.protos)do _resolve_strings(sub,S)end
  end
  _vm_run=function(blob,isa_map,S)
    local magic=string.char(blob[1],blob[2],blob[3],blob[4])
    if magic~='LUOB' then return end
    local proto,_=_deserialize(blob,14)
    _resolve_strings(proto,S)
    _exec(proto,isa_map,nil,{})
  end
end