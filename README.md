# LowPy

> Python-syntax systems programming language targeting UEFI and OS development, compiling via QBE IR.  
> No GC. No heap by default. No vtables. No hidden runtime overhead.

---

## What is LowPy?

LowPy is a compiled systems programming language with Python-like syntax. It is designed for low-level targets — bootloaders, UEFI firmware, operating systems, embedded systems, and bare-metal environments — where a traditional runtime is either unavailable or undesirable.

The goal is to explore a simple question:

> *Can modern compiler capabilities be combined with a strict runtime-free-by-default philosophy?*

LowPy does not reject modern language features. It carefully selects which ones can be implemented without hidden costs, and defers the rest to explicit opt-in layers.

---

## Pipeline

```
.lpy  →  Lexer  →  Token Preprocessor  →  Parser  →  AST  →  QBE IR  →  Binary
```

- **Lexer** — tokenizes LowPy source, handles indentation, generics substitution hints, dunder methods
- **Token Preprocessor** — compile-time generic substitution at the token level (not AST-level)
- **Parser** — recursive descent, produces a typed AST
- **IR Emitter** — walks the AST and emits [QBE IR](https://c9x.me/compile/)
- **QBE** — lightweight compiler backend producing x86-64, ARM64, or RISC-V binaries

Phase 1 is implemented entirely in Python. QBE integration is via Python bindings — a dedicated module that either wraps QBE's C API or emits QBE IR as text and invokes the `qbe` binary.

---

## Project Structure

```
lowpy-python/
├── src/
│   └── lexer/
│       ├── __init__.py
│       ├── keywords.py       # keyword table and classification
│       └── lexer.py          # main tokenizer
├── tests/
│   └── lexer/
│       ├── basic.lpy         # basic syntax test cases
│       ├── errors.lpy        # error recovery tests
│       ├── numbers.lpy       # numeric literal tests
│       ├── strings.lpy       # string literal tests
│       ├── uefi_example.lpy  # real UEFI-target example
│       └── *.snap / *.txt    # snapshot outputs for diffing
├── cpp/                      # reserved for future C++ interop / FFI layer
├── main.py                   # CLI entrypoint
├── pyproject.toml
└── uv.lock
```

---

## Current Status

| Component            | Status                            |
|----------------------|-----------------------------------|
| Lexer                | ✅ ~90% complete                   |
| Token Preprocessor   | 🔄 In progress                    |
| Parser               | ⏳ Not started (next milestone)    |
| AST Node definitions | ⏳ Not started                     |
| QBE IR Emitter       | ⏳ Not started                     |
| QBE Python Bindings  | ⏳ Planned (Phase 1)               |

---

## Design Philosophy

LowPy is built around the idea that a systems programming language does not need to depend on a runtime by default to be modern, expressive, or powerful.

### The Compiler Assists — It Does Not Dominate

The compiler leverages static analysis, type inference, escape analysis, IR-level optimization, and compile-time metaprogramming. None of these produce side effects the programmer cannot see.

- Explicit programmer control is preserved at all times
- No hidden allocations or invisible behavior
- ABI transparency is a first-class concern
- Predictable execution is non-negotiable
- 100% C-compatible readability — every construct maps cleanly to a C mental model

### Runtime-Free by Default — Four Layers

LowPy separates concerns into explicit opt-in layers. Nothing above Layer 0 is ever implicitly included.

| Layer   | Description                                              |
|---------|----------------------------------------------------------|
| Layer 0 | Bare metal — no runtime, no heap, no hidden init         |
| Layer 1 | Optional allocators (arena, explicit memory strategies)  |
| Layer 2 | Optional async / concurrency systems                     |
| Layer 3 | Optional managed / higher-level abstractions             |

This constraint forces important architectural questions at design time: *What truly requires runtime support? What can be resolved at compile time? Which abstractions are genuinely zero-cost?*

---

## Language Snapshot

```python
# Functions
def add(a: i32, b: i32) -> i32:
    return a + b

# Pointer types  —  @ is the pointer sigil, never chained
def set_value(ptr: @i32, val: i32):
    *ptr = val       # * = dereference
    addr = &val      # & = address-of (works for data and functions)

# type = pure data struct
type Point:
    x: f32
    y: f32

# class = struct + implicit self  (compiler rewrites to free functions, no vtables)
class Vec2:
    x: f32
    y: f32

    def length(self) -> f32:
        return sqrt(self.x * self.x + self.y * self.y)

# Static array — C-style initializer
buf: i32[10] = {}

# Const string goes to .rodata
msg: const str = "hello, world"

# Struct memory layout directive
__layout__(packed)
type PackedHeader:
    magic:   u16
    version: u8
    flags:   u8
```

### Key Syntax Decisions

| Feature          | LowPy                                          |
|------------------|------------------------------------------------|
| Pointer sigil    | `@T` (never chained)                           |
| Dereference      | `*ptr`                                         |
| Address-of       | `&val` — uniform for data and functions        |
| Functions        | `def`                                          |
| Comments         | `#`                                            |
| Booleans         | `true` / `false`                               |
| Pure struct      | `type`                                         |
| Struct + methods | `class` (no vtables, no RTTI)                  |
| Memory layout    | `__layout__(packed \| aligned(N) \| endian)`   |
| Generics         | Token-level substitution (comptime in Phase 2) |
| Typing           | Structural (not nominal)                       |
| Dynamic dispatch | Not supported                                  |

---

## Roadmap

### Phase 1 — Pure Python (Current)
The entire compiler toolchain is written in Python. The goal is a working end-to-end `.lpy → binary` pipeline.

- Lexer, parser, semantic analysis, and IR emission all in Python
- QBE integration via Python bindings (C API wrapper or text IR + subprocess)
- libc-dependent: all system calls go through libc
- Static allocation and stack only — no heap GC

### Phase 2 — Arena GC + Opt-in Runtime
- Arena-based garbage collector
- Opt-in runtime library
- Comptime evaluation (Zig-inspired)
- Inline assembly (`asm:` block)
- Tagged union support (`union SmallValue`)
- Ownership / borrowing rules (design pending)

### Phase 3 — Own libc + Direct Syscalls
- Remove libc dependency entirely
- Direct syscall interface
- Full UEFI / OS-level / bare-metal support

---

## Target Domains

- UEFI firmware and bootloaders
- Operating system kernels
- Embedded systems
- Compilers and low-level tooling
- Anything where a runtime is a liability, not a feature

---

## Getting Started

> The project is in early development. The lexer is functional and test snapshots are available.

**Requirements:** Python 3.14+, [uv](https://github.com/astral-sh/uv)

```bash
git clone https://github.com/your-username/lowpy-python
cd lowpy-python
uv sync
python main.py
```

Lexer snapshot tests live in `tests/lexer/`. Each `.lpy` file has a corresponding `.snap` (token snapshot) and `.lpy.txt` (expected output) for diffing.

---

## A Note on This Project

This is a **hobby project** — built for the joy of building it. There is no shipping deadline, no roadmap pressure, and no definition of success beyond having fun in the process.

I use AI assistance throughout — for brainstorming language design decisions, thinking through tradeoffs, and occasionally for lite coding tasks. The ideas, direction, and final calls are mine; AI is a thinking partner, not a ghostwriter.

If that bothers you, this project probably isn't for you. If it doesn't — welcome aboard.

---

## Documentation

Full language design documentation — type system, vargs, lexer internals, design philosophy, and roadmap — is maintained in the LowPy Notion Wiki:

📖 [LowPy Wiki](https://www.notion.so/LowPy-Wiki-363c7b111117810381a6ebab41938b9d)

---

## License

Licensed under the [Apache License 2.0](./LICENSE).
