import os

VM_TEMPLATE_PATH=os.path.join(os.path.dirname(__file__),'vm_template.lua')

def _load_vm():
    with open(VM_TEMPLATE_PATH,'r',encoding='utf-8') as f:return f.read()

def _blob_literal(blob):
    rows=[]
    for i in range(0,len(blob),16):rows.append(','.join(str(b) for b in blob[i:i+16]))
    return '{'+','.join(rows)+'}'

def _isa_map_literal(isa):
    pairs=[f'[{byte}]="{op.name}"' for op,byte in isa.encode.items()]
    return '{'+','.join(pairs)+'}'

def _enc_string_table(enc_strings):
    if not enc_strings:return 'local __S={}'
    lines=['local __S={}','do']
    for idx,(original,cipher,key) in enumerate(enc_strings):
        k_lit='{'+','.join(str(b) for b in key)+'}'
        c_lit='{'+','.join(str(b) for b in cipher)+'}'
        lines.append(f'  __S[{idx}]=(function()local k={k_lit};local c={c_lit};local r={{}};'
            f'for i=1,#c do r[i]=string.char(bit32.bxor(c[i],k[((i-1)%#k)+1]))end;'
            f'local s=table.concat(r);__S[{idx}]=function()return s end;return s end)')
    lines.append('end');return '\n'.join(lines)

def emit(blob,isa,enc_strings,env_check,integrity_check,anti_debug,banner=''):
    vm_src=_load_vm();blob_lit=_blob_literal(blob)
    isa_lit=_isa_map_literal(isa);str_tbl=_enc_string_table(enc_strings)
    parts=[]
    if banner:parts.append(f'-- {banner}')
    parts.append(env_check);parts.append('')
    parts.append(anti_debug);parts.append('')
    parts.append(str_tbl);parts.append('')
    parts.append(vm_src);parts.append('')
    parts.append(f'local __b={blob_lit}')
    parts.append(f'local __m={isa_lit}');parts.append('')
    parts.append(integrity_check);parts.append('')
    parts.append('_vm_run(__b,__m,__S)')
    return '\n'.join(parts)