from src.lexer.lexer import Lexer
from src.parser.parser import Parser



source = [
    "x: i32 = 5",
    "y: f32 = 3.14",
    "name: str = some_var",
    "flag: bool = other",
    "x: const i32 = 10",
    "items: list<i32> = mylist",
    "map: list<list<i32>> = nested",
    "x: i32<str> = 5",  # primitive with generic args
    "x: i32 5",  # missing =
    "x i32 = 5",  # missing :
    "x: = 5",  # missing type
    "x: list<> = y"  # empty generic args
]

for line in source:
    print(f"Parsing: {line}")
    tokens = list(Lexer(line))
    parser = Parser(tokens)
    result = parser.parse()
    if result is not None:
        for r in result:
            if r is not None:
                print(f"{r.kind} kind to dict: {r.to_dict()}")
    print(result)
    print("-" * 40)