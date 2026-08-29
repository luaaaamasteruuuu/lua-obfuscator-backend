from .ast_nodes import *
from .isa import Op,Proto
from .string_enc import StringEncryptor

class CompileError(Exception):pass

class Scope:
    def __init__(self,parent=None):
        self.parent=parent;self.locals={}
        self.slot=parent.slot if parent else 0
    def define(self,name):
        idx=self.slot;self.locals[name]=idx;self.slot+=1;return idx
    def lookup(self,name):
        if name in self.locals:return('local',self.locals[name])
        if self.parent:return self.parent.lookup(name)
        return None

class Compiler:
    def __init__(self,seed=None):
        self.proto=None;self.scope=None;self.breaks=[];self.conts=[]
        self.str_enc=StringEncryptor(seed=seed)
        self.enc_strings=[];self._enc_index={}
    def compile(self,chunk):
        p=Proto();p.vararg=True;self._enter(p)
        self._block(chunk.body);self._emit(Op.RETURN,0);self._leave()
        p.enc_strings=self.enc_strings;return p
    def _register_enc_string(self,s):
        if s in self._enc_index:return self._enc_index[s]
        cipher,key=self.str_enc.encrypt(s)
        idx=len(self.enc_strings);self.enc_strings.append((s,cipher,key))
        self._enc_index[s]=idx;return idx
    def _enter(self,proto):self.proto=proto;self.scope=Scope()
    def _leave(self):pass
    def _push_scope(self):self.scope=Scope(self.scope)
    def _pop_scope(self):self.scope=self.scope.parent
    def _emit(self,op,arg=0,arg2=0):return self.proto.emit(op,arg,arg2)
    def _const(self,v):return self.proto.add_const(v)
    def _pc(self):return len(self.proto.code)
    def _patch(self,idx,target=None):self.proto.patch(idx,target if target is not None else self._pc())
    def _block(self,stmts):
        self._push_scope()
        for s in stmts:self._stmt(s)
        self._pop_scope()
    def _stmt(self,s):
        t=type(s)
        if t is AssignStmt:self._assign(s)
        elif t is LocalStmt:self._local(s)
        elif t is CallStmt:self._expr(s.call);self._emit(Op.POP)
        elif t is DoStmt:self._block(s.body)
        elif t is WhileStmt:self._while(s)
        elif t is RepeatStmt:self._repeat(s)
        elif t is IfStmt:self._if(s)
        elif t is NumericFor:self._num_for(s)
        elif t is GenericFor:self._gen_for(s)
        elif t is FunctionStmt:self._func_stmt(s)
        elif t is LocalFunctionStmt:self._local_func(s)
        elif t is ReturnStmt:self._return(s)
        elif t is BreakStmt:self._break()
        elif t is ContinueStmt:self._continue()
    def _assign(self,s):
        for v in s.values:self._expr(v)
        for _ in range(len(s.targets)-len(s.values)):self._emit(Op.PUSH_NIL)
        for target in reversed(s.targets):self._assign_target(target)
    def _assign_target(self,target):
        if isinstance(target,NameExpr):
            res=self.scope.lookup(target.name)
            if res and res[0]=='local':self._emit(Op.SET_LOCAL,res[1])
            else:self._emit(Op.SET_GLOBAL,self._const(target.name))
        elif isinstance(target,IndexExpr):
            self._expr(target.table);self._expr(target.key);self._emit(Op.SET_TABLE)
        elif isinstance(target,FieldExpr):
            self._expr(target.table);self._emit(Op.SET_FIELD,self._const(target.field))
    def _local(self,s):
        for i,name in enumerate(s.names):
            if i<len(s.values):self._expr(s.values[i])
            else:self._emit(Op.PUSH_NIL)
            self._emit(Op.SET_LOCAL,self.scope.define(name))
    def _while(self,s):
        loop_start=self._pc();self._expr(s.cond)
        exit_jmp=self._emit(Op.JMP_FALSE,0)
        self.breaks.append([]);self.conts.append([])
        self._block(s.body)
        for ci in self.conts.pop():self._patch(ci,loop_start)
        self._emit(Op.JMP,loop_start);self._patch(exit_jmp)
        for bi in self.breaks.pop():self._patch(bi)
    def _repeat(self,s):
        loop_start=self._pc()
        self.breaks.append([]);self.conts.append([])
        self._block(s.body)
        for ci in self.conts.pop():self._patch(ci)
        self._expr(s.cond);self._emit(Op.JMP_FALSE,loop_start)
        for bi in self.breaks.pop():self._patch(bi)
    def _if(self,s):
        ends=[];self._expr(s.cond)
        next_jmp=self._emit(Op.JMP_FALSE,0)
        self._block(s.then);ends.append(self._emit(Op.JMP,0));self._patch(next_jmp)
        for(ec,eb) in s.elseifs:
            self._expr(ec);next_jmp=self._emit(Op.JMP_FALSE,0)
            self._block(eb);ends.append(self._emit(Op.JMP,0));self._patch(next_jmp)
        if s.else_:self._block(s.else_)
        for e in ends:self._patch(e)
    def _num_for(self,s):
        self._expr(s.start);self._expr(s.stop)
        if s.step:self._expr(s.step)
        else:self._emit(Op.PUSH_NUMBER,self._const(1))
        loop_start=self._pc();exit_jmp=self._emit(Op.LOOP,0)
        slot=self.scope.define(s.var);self._emit(Op.SET_LOCAL,slot)
        self.breaks.append([]);self.conts.append([])
        self._block(s.body)
        for ci in self.conts.pop():self._patch(ci,loop_start)
        self._emit(Op.JMP,loop_start);self._patch(exit_jmp)
        for bi in self.breaks.pop():self._patch(bi)
    def _gen_for(self,s):
        for it in s.iters:self._expr(it)
        loop_start=self._pc()
        self._emit(Op.CALL_MULTI,len(s.iters),len(s.vars))
        exit_jmp=self._emit(Op.JMP_FALSE,0)
        self.breaks.append([]);self.conts.append([])
        self._push_scope()
        for v in s.vars:self._emit(Op.SET_LOCAL,self.scope.define(v))
        self._block(s.body);self._pop_scope()
        for ci in self.conts.pop():self._patch(ci,loop_start)
        self._emit(Op.JMP,loop_start);self._patch(exit_jmp)
        for bi in self.breaks.pop():self._patch(bi)
    def _func_stmt(self,s):self._compile_func(s.func);self._assign_target(s.name)
    def _local_func(self,s):
        slot=self.scope.define(s.name);self._compile_func(s.func);self._emit(Op.SET_LOCAL,slot)
    def _return(self,s):
        for v in s.values:self._expr(v);self._emit(Op.RETURN,len(s.values))
    def _break(self):self.breaks[-1].append(self._emit(Op.JMP,0))
    def _continue(self):self.conts[-1].append(self._emit(Op.JMP,0))
    def _expr(self,e):
        t=type(e)
        if t is NilExpr:self._emit(Op.PUSH_NIL)
        elif t is TrueExpr:self._emit(Op.PUSH_TRUE)
        elif t is FalseExpr:self._emit(Op.PUSH_FALSE)
        elif t is NumberExpr:self._emit(Op.PUSH_NUMBER,self._const(e.value))
        elif t is StringExpr:
            ei=self._register_enc_string(e.value)
            self._emit(Op.PUSH_STRING,self._const(f'\x00ENC:{ei}'))
        elif t is VarArgExpr:self._emit(Op.PUSH_VARARG)
        elif t is NameExpr:self._name(e.name)
        elif t is FieldExpr:
            self._expr(e.table);ei=self._register_enc_string(e.field)
            self._emit(Op.GET_FIELD,self._const(f'\x00ENC:{ei}'))
        elif t is IndexExpr:self._expr(e.table);self._expr(e.key);self._emit(Op.GET_TABLE)
        elif t is BinopExpr:self._binop(e)
        elif t is UnopExpr:self._unop(e)
        elif t is CallExpr:self._call(e)
        elif t is MethodCallExpr:self._method(e)
        elif t is FunctionExpr:self._compile_func(e)
        elif t is TableConstructor:self._table(e)
    def _name(self,name):
        res=self.scope.lookup(name)
        if res and res[0]=='local':self._emit(Op.PUSH_LOCAL,res[1])
        else:self._emit(Op.PUSH_GLOBAL,self._const(name))
    def _binop(self,e):
        op_map={'+':Op.ADD,'-':Op.SUB,'*':Op.MUL,'/':Op.DIV,'%':Op.MOD,'^':Op.POW,
            '//':Op.IDIV,'&':Op.BAND,'|':Op.BOR,'~':Op.BXOR,'<<':Op.SHL,'>>':Op.SHR,
            '..':Op.CONCAT,'==':Op.EQ,'~=':Op.NEQ,'<':Op.LT,'<=':Op.LE,'>':Op.GT,'>=':Op.GE}
        if e.op=='and':
            self._expr(e.left);jmp=self._emit(Op.JMP_FALSE,0)
            self._emit(Op.POP);self._expr(e.right);self._patch(jmp)
        elif e.op=='or':
            self._expr(e.left);self._emit(Op.DUP);jmp=self._emit(Op.JMP_TRUE,0)
            self._emit(Op.POP);self._expr(e.right);self._patch(jmp)
        else:
            self._expr(e.left);self._expr(e.right);self._emit(op_map[e.op])
    def _unop(self,e):
        self._expr(e.operand);self._emit({'not':Op.NOT,'-':Op.UNM,'#':Op.LEN,'~':Op.BNOT}[e.op])
    def _call(self,e):
        self._expr(e.func)
        for a in e.args:self._expr(a)
        self._emit(Op.CALL,len(e.args))
    def _method(self,e):
        self._expr(e.obj);ki=self._const(e.method)
        for a in e.args:self._expr(a)
        self._emit(Op.METHOD,ki,len(e.args))
    def _table(self,e):
        self._emit(Op.NEW_TABLE)
        for i,(k,v) in enumerate(e.fields):
            self._emit(Op.DUP)
            if k is None:self._emit(Op.PUSH_NUMBER,self._const(i+1))
            else:self._expr(k)
            self._expr(v);self._emit(Op.SET_TABLE)
    def _compile_func(self,fe):
        outer_proto=self.proto;outer_scope=self.scope
        p=Proto();p.params=len(fe.params);p.vararg=fe.vararg
        self.proto=p;self.scope=Scope()
        for param in fe.params:self.scope.define(param);p.locals.append(param)
        self._block(fe.body);self._emit(Op.RETURN,0)
        idx=outer_proto.add_proto(p);self.proto=outer_proto;self.scope=outer_scope
        self._emit(Op.PUSH_CLOSURE,idx)