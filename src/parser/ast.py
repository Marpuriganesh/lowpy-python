from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Optional

class BaseNode:
    kind: str = "BaseNode"
    def to_dict(self):
        return asdict(self)

class Expression(BaseNode):
    pass

@dataclass
class IntLiteral(Expression):
    value: int
    kind: str = field(default="IntLiteral", init=False)

@dataclass
class FloatLiteral(Expression):
    value: float
    kind: str = field(default="FloatLiteral", init=False)

@dataclass
class Identifier(Expression):
    name: str
    kind: str = field(default="Identifier", init=False)
    

@dataclass
class TypeNode(BaseNode):
    name: str
    is_pointer: bool = False
    generic_args: Optional[List[TypeNode]] = None
    kind: str = field(default="TypeNode", init=False)

@dataclass
class VarDecl(BaseNode):
    name: str
    type: TypeNode
    value: Expression
    is_const: bool
    kind: str = field(default="VarDecl", init=False)
    
