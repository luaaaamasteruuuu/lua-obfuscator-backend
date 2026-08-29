import random,string
from .ast_nodes import *

LUAU_KEYWORDS={'and','break','do','else','elseif','end','false','for',
    'function','if','in','local','nil','not','or','repeat',
    'return','then','true','until','while','continue'}

def _rand_name(rng,length=8):
    while True:
        n='_'+''.join(rng.choices(string.ascii_letters+string.digits,k=length))
        if n not in LUAU_KEYWORDS:return n

class NameMap:
    def __init__(self,parent=None):self.parent=parent;self.mapping={}
    def define(self,original,mangled):self.mapping[original]=mangled
    def lookup(self,name):
        if name in self.mapping:return self.mapping[name]
        if self.parent:return self.parent.lookup(name)
        return None
    def child(self):return NameMap(self)

class NameMangler:
    def __init__(self,seed=None):self.rng=random.Random(seed);self.scope=NameMap()
    def mangle(self,node):
        if isinstance(node,Chunk):
            for s in node.body:self._stmt(s,self.scope)
        return node
    def _stmt(self,s,scope):
        t=type(s)
        if t is LocalStmt:
            for v in s.values:self._expr(v,scope)
            for i,name in enumerate(s.names):
                m=_rand_name(self.rng);scope.define(name,m);s.names[i]=m
        elif t is LocalFunctionStmt:
            m=_rand_name(self.rng);scope.define(s.name,m);s.name=m;self._func(s.func,scope)
        elif t is FunctionStmt:self._func(s.func,scope)
        elif t is AssignStmt:
            for v in s.values:self._expr(v,scope)
            for tgt in s.targets:self._expr(tgt,scope)
        elif t is CallStmt:self._expr(s.call,scope)
        elif t is DoStmt:
            child=scope.child()
            for st in s.body:self._stmt(st,child)
        elif t is WhileStmt:
            self._expr(s.cond,scope);child=scope.child()
            for st in s.body:self._stmt(st,child)
        elif t is RepeatStmt:
            child=scope.child()
            for st in s.body:self._stmt(st,child)
            self._expr(s.cond,child)
        elif t is IfStmt:
            self._expr(s.cond,scope);child=scope.child()
            for st in s.then:self._stmt(st,child)
            for(ec,eb) in s.elseifs:
                self._expr(ec,scope);c2=scope.child()
                for st in eb:self._stmt(st,c2)
            if s.else_:
                c3=scope.child()
                for st in s.else_:self._stmt(st,c3)
        elif t is NumericFor:
            self._expr(s.start,scope);self._expr(s.stop,scope)
            if s.step:self._expr(s.step,scope)
            child=scope.child();m=_rand_name(self.rng);child.define(s.var,m);s.var=m
            for st in s.body:self._stmt(st,child)
        elif t is GenericFor:
            for it in s.iters:self._expr(it,scope)
            child=scope.child()
            for i,v in enumerate(s.vars):
                m=_rand_name(self.rng);child.define(v,m);s.vars[i]=m
            for st in s.body:self._stmt(st,child)
        elif t is ReturnStmt:
            for v in s.values:self._expr(v,scope)
    def _expr(self,e,scope):
        t=type(e)
        if t is NameExpr:
            m=scope.lookup(e.name)
            if m:e.name=m
        elif t is FieldExpr:self._expr(e.table,scope)
        elif t is IndexExpr:self._expr(e.table,scope);self._expr(e.key,scope)
        elif t is CallExpr:
            self._expr(e.func,scope)
            for a in e.args:self._expr(a,scope)
        elif t is MethodCallExpr:
            self._expr(e.obj,scope)
            for a in e.args:self._expr(a,scope)
        elif t is BinopExpr:self._expr(e.left,scope);self._expr(e.right,scope)
        elif t is UnopExpr:self._expr(e.operand,scope)
        elif t is FunctionExpr:self._func(e,scope)
        elif t is TableConstructor:
            for(k,v) in e.fields:
                if k is not None:self._expr(k,scope)
                self._expr(v,scope)
    def _func(self,fe,parent_scope):
        child=parent_scope.child()
        for i,p in enumerate(fe.params):
            m=_rand_name(self.rng);child.define(p,m);fe.params[i]=m
        for s in fe.body:self._stmt(s,child)