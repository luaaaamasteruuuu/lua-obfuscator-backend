import re
from enum import Enum, auto

class TT(Enum):
    NUMBER=auto();STRING=auto();NAME=auto()
    AND=auto();BREAK=auto();DO=auto();ELSE=auto()
    ELSEIF=auto();END=auto();FALSE=auto();FOR=auto()
    FUNCTION=auto();IF=auto();IN=auto();LOCAL=auto()
    NIL=auto();NOT=auto();OR=auto();REPEAT=auto()
    RETURN=auto();THEN=auto();TRUE=auto();UNTIL=auto()
    WHILE=auto();CONTINUE=auto()
    PLUS=auto();MINUS=auto();STAR=auto();SLASH=auto()
    PERCENT=auto();CARET=auto();HASH=auto();AMPERSAND=auto()
    TILDE=auto();PIPE=auto();LSHIFT=auto();RSHIFT=auto()
    DSLASH=auto();EQ=auto();NEQ=auto();LT=auto();GT=auto()
    LEQ=auto();GEQ=auto();LPAREN=auto();RPAREN=auto()
    LBRACE=auto();RBRACE=auto();LBRACKET=auto();RBRACKET=auto()
    DCOLON=auto();SEMI=auto();COLON=auto();COMMA=auto()
    DOT=auto();DOTDOT=auto();DOTDOTDOT=auto();ASSIGN=auto()
    ARROW=auto();EOF=auto()

KEYWORDS={
    'and':TT.AND,'break':TT.BREAK,'do':TT.DO,'else':TT.ELSE,
    'elseif':TT.ELSEIF,'end':TT.END,'false':TT.FALSE,'for':TT.FOR,
    'function':TT.FUNCTION,'if':TT.IF,'in':TT.IN,'local':TT.LOCAL,
    'nil':TT.NIL,'not':TT.NOT,'or':TT.OR,'repeat':TT.REPEAT,
    'return':TT.RETURN,'then':TT.THEN,'true':TT.TRUE,'until':TT.UNTIL,
    'while':TT.WHILE,'continue':TT.CONTINUE,
}

class Token:
    def __init__(self,type,value,line):
        self.type=type;self.value=value;self.line=line

class LexError(Exception):pass

class Lexer:
    def __init__(self,src):
        self.src=src;self.pos=0;self.line=1;self.tokens=[]
    def peek(self,o=0):
        i=self.pos+o;return self.src[i] if i<len(self.src) else '\0'
    def advance(self):
        ch=self.src[self.pos];self.pos+=1
        if ch=='\n':self.line+=1
        return ch
    def match(self,ch):
        if self.pos<len(self.src) and self.src[self.pos]==ch:
            self.pos+=1;return True
        return False
    def skip_whitespace_and_comments(self):
        while self.pos<len(self.src):
            ch=self.peek()
            if ch in ' \t\r\n':self.advance()
            elif ch=='-' and self.peek(1)=='-':
                self.pos+=2
                if self.peek()=='[':
                    level=self._long_bracket_level()
                    if level>=0:self._read_long_string(level);continue
                while self.pos<len(self.src) and self.peek()!='\n':self.pos+=1
            else:break
    def _long_bracket_level(self):
        i=self.pos+1;level=0
        while i<len(self.src) and self.src[i]=='=':level+=1;i+=1
        if i<len(self.src) and self.src[i]=='[':return level
        return -1
    def _read_long_string(self,level):
        close=']'+'='*level+']';self.pos+=2+level
        start=self.pos
        while self.pos<len(self.src):
            idx=self.src.find(close,self.pos)
            if idx==-1:raise LexError("unfinished long string")
            for ch in self.src[self.pos:idx]:
                if ch=='\n':self.line+=1
            content=self.src[start:idx];self.pos=idx+len(close);return content
        raise LexError("unfinished long string")
    def read_string(self,delim):
        result=[]
        while self.pos<len(self.src):
            ch=self.advance()
            if ch==delim:return ''.join(result)
            if ch=='\\':
                esc=self.advance()
                result.append({'n':'\n','t':'\t','r':'\r','\\':'\\',
                    "'":"'",'\"':'"','a':'\a','b':'\b'}.get(esc,esc))
            elif ch=='\n':raise LexError(f"unfinished string at line {self.line}")
            else:result.append(ch)
        raise LexError("unfinished string")
    def read_number(self):
        start=self.pos-1
        while self.pos<len(self.src) and (self.src[self.pos].isalnum() or self.src[self.pos] in '._'):
            self.pos+=1
        raw=self.src[start:self.pos]
        try:return float(raw) if '.' in raw or 'e' in raw.lower() else int(raw,0)
        except:return raw
    def tokenize(self):
        while True:
            self.skip_whitespace_and_comments()
            if self.pos>=len(self.src):
                self.tokens.append(Token(TT.EOF,None,self.line));break
            line=self.line;ch=self.advance()
            if ch.isdigit() or (ch=='.' and self.peek().isdigit()):
                self.tokens.append(Token(TT.NUMBER,self.read_number(),line))
            elif ch.isalpha() or ch=='_':
                start=self.pos-1
                while self.pos<len(self.src) and (self.src[self.pos].isalnum() or self.src[self.pos]=='_'):
                    self.pos+=1
                word=self.src[start:self.pos]
                self.tokens.append(Token(KEYWORDS.get(word,TT.NAME),word,line))
            elif ch in('"',"'"):
                self.tokens.append(Token(TT.STRING,self.read_string(ch),line))
            elif ch=='[' and self.peek() in('[','='):
                level=self._long_bracket_level()
                if level>=0:
                    self.pos-=1;s=self._read_long_string(level)
                    self.tokens.append(Token(TT.STRING,s,line))
                else:self.tokens.append(Token(TT.LBRACKET,'[',line))
            else:
                sym={'+':TT.PLUS,'-':TT.MINUS,'*':TT.STAR,'%':TT.PERCENT,
                    '^':TT.CARET,'#':TT.HASH,'&':TT.AMPERSAND,'|':TT.PIPE,
                    '(':TT.LPAREN,')':TT.RPAREN,'{':TT.LBRACE,'}':TT.RBRACE,
                    ']':TT.RBRACKET,';':TT.SEMI,',':TT.COMMA}
                if ch in sym:self.tokens.append(Token(sym[ch],ch,line))
                elif ch=='/':self.tokens.append(Token(TT.DSLASH if self.match('/') else TT.SLASH,ch,line))
                elif ch=='~':self.tokens.append(Token(TT.NEQ if self.match('=') else TT.TILDE,ch,line))
                elif ch=='<':
                    if self.match('<'):self.tokens.append(Token(TT.LSHIFT,'<<',line))
                    elif self.match('='):self.tokens.append(Token(TT.LEQ,'<=',line))
                    else:self.tokens.append(Token(TT.LT,'<',line))
                elif ch=='>':
                    if self.match('>'):self.tokens.append(Token(TT.RSHIFT,'>>',line))
                    elif self.match('='):self.tokens.append(Token(TT.GEQ,'>=',line))
                    else:self.tokens.append(Token(TT.GT,'>',line))
                elif ch=='=':
                    if self.match('='):self.tokens.append(Token(TT.EQ,'==',line))
                    else:self.tokens.append(Token(TT.ASSIGN,'=',line))
                elif ch==':':self.tokens.append(Token(TT.DCOLON if self.match(':') else TT.COLON,ch,line))
                elif ch=='.':
                    if self.match('.'):
                        self.tokens.append(Token(TT.DOTDOTDOT if self.match('.') else TT.DOTDOT,'..',line))
                    else:self.tokens.append(Token(TT.DOT,'.',line))
                else:raise LexError(f"unexpected char {ch!r} at line {line}")
        return self.tokens