from dataclasses import dataclass, field
from typing import Any, List, Optional

@dataclass
class NilExpr: pass
@dataclass
class TrueExpr: pass
@dataclass
class FalseExpr: pass
@dataclass
class NumberExpr:
    value: Any
@dataclass
class StringExpr:
    value: str
@dataclass
class VarArgExpr: pass
@dataclass
class NameExpr:
    name: str
@dataclass
class IndexExpr:
    table: Any
    key: Any
@dataclass
class FieldExpr:
    table: Any
    field: str
@dataclass
class MethodCallExpr:
    obj: Any
    method: str
    args: List[Any]
@dataclass
class CallExpr:
    func: Any
    args: List[Any]
@dataclass
class BinopExpr:
    op: str
    left: Any
    right: Any
@dataclass
class UnopExpr:
    op: str
    operand: Any
@dataclass
class FunctionExpr:
    params: List[str]
    vararg: bool
    body: List[Any]
@dataclass
class TableConstructor:
    fields: List[Any]
@dataclass
class AssignStmt:
    targets: List[Any]
    values: List[Any]
@dataclass
class LocalStmt:
    names: List[str]
    attribs: List[Optional[str]]
    values: List[Any]
@dataclass
class DoStmt:
    body: List[Any]
@dataclass
class WhileStmt:
    cond: Any
    body: List[Any]
@dataclass
class RepeatStmt:
    body: List[Any]
    cond: Any
@dataclass
class IfStmt:
    cond: Any
    then: List[Any]
    elseifs: List[Any]
    else_: Optional[List[Any]]
@dataclass
class NumericFor:
    var: str
    start: Any
    stop: Any
    step: Optional[Any]
    body: List[Any]
@dataclass
class GenericFor:
    vars: List[str]
    iters: List[Any]
    body: List[Any]
@dataclass
class FunctionStmt:
    name: Any
    method: bool
    func: Any
@dataclass
class LocalFunctionStmt:
    name: str
    func: Any
@dataclass
class ReturnStmt:
    values: List[Any]
@dataclass
class BreakStmt: pass
@dataclass
class ContinueStmt: pass
@dataclass
class CallStmt:
    call: Any
@dataclass
class Chunk:
    body: List[Any]