from .lexer import TT,Token
from .ast_nodes import *

class ParseError(Exception):pass

class Parser:
    def __init__(self,tokens):
        self.tokens=tokens;self.pos=0
    def peek(self):return self.tokens[self.pos]
    def prev(self):return self.tokens[self.pos-1]
    def check(self,*types):return self.peek().type in types
    def advance(self):
        t=self.tokens[self.pos]
        if t.type!=TT.EOF:self.pos+=1
        return t
    def expect(self,tt,msg=None):
        if self.check(tt):return self.advance()
        t=self.peek();raise ParseError(msg or f"expected {tt} got {t.type} line {t.line}")
    def match(self,*types):
        if self.check(*types):return self.advance()
        return None
    def parse(self):
        body=self.parse_block();self.expect(TT.EOF);return Chunk(body)
    def parse_block(self):
        stmts=[]
        while True:
            self.skip_semis()
            if self.check(TT.EOF,TT.END,TT.ELSE,TT.ELSEIF,TT.UNTIL):break
            s=self.parse_stmt()
            if s is None:break
            stmts.append(s)
            if isinstance(s,ReturnStmt):break
        return stmts
    def skip_semis(self):
        while self.match(TT.SEMI):pass
    def parse_stmt(self):
        t=self.peek()
        if t.type==TT.IF:return self.parse_if()
        if t.type==TT.WHILE:return self.parse_while()
        if t.type==TT.DO:return self.parse_do()
        if t.type==TT.FOR:return self.parse_for()
        if t.type==TT.REPEAT:return self.parse_repeat()
        if t.type==TT.FUNCTION:return self.parse_function_stmt()
        if t.type==TT.LOCAL:return self.parse_local()
        if t.type==TT.RETURN:return self.parse_return()
        if t.type==TT.BREAK:self.advance();return BreakStmt()
        if t.type==TT.CONTINUE:self.advance();return ContinueStmt()
        return self.parse_expr_stat()
    def parse_if(self):
        self.expect(TT.IF);cond=self.parse_expr();self.expect(TT.THEN)
        then=self.parse_block();elseifs=[];else_=None
        while self.check(TT.ELSEIF):
            self.advance();ec=self.parse_expr();self.expect(TT.THEN)
            elseifs.append((ec,self.parse_block()))
        if self.match(TT.ELSE):else_=self.parse_block()
        self.expect(TT.END);return IfStmt(cond,then,elseifs,else_)
    def parse_while(self):
        self.expect(TT.WHILE);cond=self.parse_expr();self.expect(TT.DO)
        body=self.parse_block();self.expect(TT.END);return WhileStmt(cond,body)
    def parse_do(self):
        self.expect(TT.DO);body=self.parse_block();self.expect(TT.END);return DoStmt(body)
    def parse_for(self):
        self.expect(TT.FOR);name=self.expect(TT.NAME).value
        if self.match(TT.ASSIGN):
            start=self.parse_expr();self.expect(TT.COMMA);stop=self.parse_expr()
            step=self.parse_expr() if self.match(TT.COMMA) else None
            self.expect(TT.DO);body=self.parse_block();self.expect(TT.END)
            return NumericFor(name,start,stop,step,body)
        else:
            names=[name]
            while self.match(TT.COMMA):names.append(self.expect(TT.NAME).value)
            self.expect(TT.IN);iters=self.parse_expr_list();self.expect(TT.DO)
            body=self.parse_block();self.expect(TT.END);return GenericFor(names,iters,body)
    def parse_repeat(self):
        self.expect(TT.REPEAT);body=self.parse_block();self.expect(TT.UNTIL)
        return RepeatStmt(body,self.parse_expr())
    def parse_function_stmt(self):
        self.expect(TT.FUNCTION);name=NameExpr(self.expect(TT.NAME).value)
        while self.match(TT.DOT):name=FieldExpr(name,self.expect(TT.NAME).value)
        method=False
        if self.match(TT.COLON):name=FieldExpr(name,self.expect(TT.NAME).value);method=True
        return FunctionStmt(name,method,self.parse_func_body(method))
    def parse_local(self):
        self.expect(TT.LOCAL)
        if self.check(TT.FUNCTION):
            self.advance();name=self.expect(TT.NAME).value
            return LocalFunctionStmt(name,self.parse_func_body(False))
        names=[self.expect(TT.NAME).value];attribs=[self.parse_attrib()]
        while self.match(TT.COMMA):names.append(self.expect(TT.NAME).value);attribs.append(self.parse_attrib())
        values=[]
        if self.match(TT.ASSIGN):values=self.parse_expr_list()
        return LocalStmt(names,attribs,values)
    def parse_attrib(self):
        if self.match(TT.LT):a=self.expect(TT.NAME).value;self.expect(TT.GT);return a
        return None
    def parse_return(self):
        self.expect(TT.RETURN);values=[]
        if not self.check(TT.END,TT.ELSE,TT.ELSEIF,TT.UNTIL,TT.EOF,TT.SEMI):values=self.parse_expr_list()
        self.match(TT.SEMI);return ReturnStmt(values)
    def parse_expr_stat(self):
        expr=self.parse_suffixed_expr()
        if self.check(TT.ASSIGN) or self.check(TT.COMMA):
            targets=[expr]
            while self.match(TT.COMMA):targets.append(self.parse_suffixed_expr())
            self.expect(TT.ASSIGN);values=self.parse_expr_list()
            return AssignStmt(targets,values)
        if isinstance(expr,(CallExpr,MethodCallExpr)):return CallStmt(expr)
        raise ParseError(f"unexpected expr stat line {self.peek().line}")
    def parse_expr_list(self):
        exprs=[self.parse_expr()]
        while self.match(TT.COMMA):exprs.append(self.parse_expr())
        return exprs
    BINOPS=[[(TT.OR,)],[(TT.AND,)],[(TT.LT,TT.GT,TT.LEQ,TT.GEQ,TT.NEQ,TT.EQ,)],
        [(TT.PIPE,)],[(TT.TILDE,)],[(TT.AMPERSAND,)],[(TT.LSHIFT,TT.RSHIFT)],
        [(TT.DOTDOT,)],[(TT.PLUS,TT.MINUS)],[(TT.STAR,TT.SLASH,TT.DSLASH,TT.PERCENT)],[(TT.CARET,)]]
    UNOPS={TT.MINUS:'-',TT.NOT:'not',TT.HASH:'#',TT.TILDE:'~'}
    def parse_expr(self,prec=0):
        if prec>=len(self.BINOPS):return self.parse_unary()
        right_assoc=(prec==len(self.BINOPS)-1)
        left=self.parse_expr(prec+1);ops=self.BINOPS[prec][0]
        while self.check(*ops):
            tok=self.advance();op=tok.value if tok.value not in('=',) else '=='
            right=self.parse_expr(prec if right_assoc else prec+1)
            left=BinopExpr(op,left,right)
        return left
    def parse_unary(self):
        if self.peek().type in self.UNOPS:
            t=self.advance();return UnopExpr(self.UNOPS[t.type],self.parse_unary())
        return self.parse_simple_expr()
    def parse_simple_expr(self):
        t=self.peek()
        if t.type==TT.NUMBER:self.advance();return NumberExpr(t.value)
        if t.type==TT.STRING:self.advance();return StringExpr(t.value)
        if t.type==TT.NIL:self.advance();return NilExpr()
        if t.type==TT.TRUE:self.advance();return TrueExpr()
        if t.type==TT.FALSE:self.advance();return FalseExpr()
        if t.type==TT.DOTDOTDOT:self.advance();return VarArgExpr()
        if t.type==TT.FUNCTION:self.advance();return self.parse_func_body(False)
        if t.type==TT.LBRACE:return self.parse_table()
        return self.parse_suffixed_expr()
    def parse_suffixed_expr(self):
        expr=self.parse_primary()
        while True:
            if self.match(TT.DOT):expr=FieldExpr(expr,self.expect(TT.NAME).value)
            elif self.check(TT.LBRACKET):
                self.advance();key=self.parse_expr();self.expect(TT.RBRACKET);expr=IndexExpr(expr,key)
            elif self.match(TT.COLON):
                method=self.expect(TT.NAME).value;args=self.parse_call_args()
                expr=MethodCallExpr(expr,method,args)
            elif self.check(TT.LPAREN,TT.LBRACE,TT.STRING):expr=CallExpr(expr,self.parse_call_args())
            else:break
        return expr
    def parse_primary(self):
        t=self.peek()
        if t.type==TT.NAME:self.advance();return NameExpr(t.value)
        if t.type==TT.LPAREN:
            self.advance();e=self.parse_expr();self.expect(TT.RPAREN);return e
        raise ParseError(f"unexpected {t.type} {t.value!r} line {t.line}")
    def parse_call_args(self):
        if self.match(TT.LPAREN):
            if self.check(TT.RPAREN):self.advance();return []
            args=self.parse_expr_list();self.expect(TT.RPAREN);return args
        if self.check(TT.LBRACE):return [self.parse_table()]
        if self.check(TT.STRING):t=self.advance();return [StringExpr(t.value)]
        raise ParseError(f"expected call args line {self.peek().line}")
    def parse_func_body(self,method):
        self.expect(TT.LPAREN);params=[];vararg=False
        if method:params.append('self')
        if not self.check(TT.RPAREN):
            if self.check(TT.DOTDOTDOT):self.advance();vararg=True
            else:
                params.append(self.expect(TT.NAME).value)
                while self.match(TT.COMMA):
                    if self.check(TT.DOTDOTDOT):self.advance();vararg=True;break
                    params.append(self.expect(TT.NAME).value)
        self.expect(TT.RPAREN)
        if self.match(TT.COLON):self._skip_type()
        body=self.parse_block();self.expect(TT.END)
        return FunctionExpr(params,vararg,body)
    def _skip_type(self):
        depth=0
        while True:
            t=self.peek()
            if t.type==TT.EOF:break
            if t.type in(TT.LPAREN,TT.LBRACE,TT.LBRACKET):depth+=1
            if t.type in(TT.RPAREN,TT.RBRACE,TT.RBRACKET):
                if depth==0:break
                depth-=1
            if depth==0 and t.type in(TT.DO,TT.THEN,TT.ASSIGN,TT.COMMA,TT.END):break
            self.advance()
    def parse_table(self):
        self.expect(TT.LBRACE);fields=[]
        while not self.check(TT.RBRACE):
            if self.check(TT.LBRACKET):
                self.advance();k=self.parse_expr();self.expect(TT.RBRACKET);self.expect(TT.ASSIGN)
                v=self.parse_expr();fields.append((k,v))
            elif self.check(TT.NAME) and self.tokens[self.pos+1].type==TT.ASSIGN:
                k=StringExpr(self.advance().value);self.expect(TT.ASSIGN)
                v=self.parse_expr();fields.append((k,v))
            else:fields.append((None,self.parse_expr()))
            if not self.match(TT.COMMA) and not self.match(TT.SEMI):break
        self.expect(TT.RBRACE);return TableConstructor(fields)