# LowPy (.lpy)

A systems programming language with Python-like syntax that compiles to C via QBE IR. Designed for UEFI/OS development where you want clean, readable code without sacrificing low-level control.

```
# This is valid LowPy
def efi_main(ImageHandle: EFI_HANDLE, SystemTable: @EFI_SYSTEM_TABLE) -> EFI_STATUS:
    SystemTable.ConOut.Reset(true)
    SystemTable.ConOut.OutputString(u"Hello from LowPy!\r\n")
    while true:
        pass
    return 0
```

---

## Design Philosophy

- **100% C-compatible** — a C programmer should read `.lpy` without needing docs
- **Clean pipeline** — `.lpy → Lexer → Parser → AST → QBE IR → QBE → binary`
- **No magic** — no vtables, no RTTI, no dynamic dispatch, no hidden allocations
- **Systems-first** — UEFI, OS kernels, embedded, network packet structures

---

## Pipeline

```
.lpy source
    └── Lexer         (Python)
    └── Parser        (Python, recursive descent)
    └── AST           (Python node classes)
    └── QBE IR emit   (Python → .ssa)
    └── QBE           (external, produces binary)
```

Backend: [QBE](https://c9x.me/compile/) — not LLVM. Lightweight, hackable, perfect for systems targets.

---

## Syntax

### Comments
```
# This is a comment
```

### Variables
```
x: UINT32 = 42
ptr: @UINT32 = &x     # ptr holds address of x
val: UINT32 = *ptr    # dereference to get 42
```

### Pointer Syntax
| Syntax | Meaning |
|--------|---------|
| `@Type` | pointer type (type position only) |
| `*ptr` | dereference |
| `&var` | address-of |

> Note: `@@` (pointer-to-pointer) is intentionally absent. `&buf` naturally creates a pointer-to-pointer situation without explicit syntax.

### Functions
```
def add(a: UINT32, b: UINT32) -> UINT32:
    return a + b
```

### Types (pure data structs)
```
type EFI_TABLE_HEADER:
    Signature:  UINT64
    Revision:   UINT32
    HeaderSize: UINT32
    CRC32:      UINT32
    Reserved:   UINT32
```

`type` is pure data — no methods, no compiler magic. Fields can be:
- Plain fields: `name: TypeName`
- Pointer fields: `vendor: @CHAR16`
- Function pointer fields: `Reset:(@EFI_SIMPLE_TEXT_OUTPUT_PROTOCOL, BOOLEAN) -> EFI_STATUS`
- Layout directives: `__layout__(packed, alignment=4)`

### Classes (struct + implicit self)
```
class Node:
    value: UINT32
    next: @Node

    def insert(self, val: UINT32):
        # compiler rewrites to free function: Node_insert(self, val)
        pass
```

`class` adds implicit `self` — the compiler rewrites methods to free functions. No vtables, no inheritance, no dynamic dispatch.

### Function Pointers on Types
```
type EFI_SIMPLE_TEXT_OUTPUT_PROTOCOL:
    Reset:(@EFI_SIMPLE_TEXT_OUTPUT_PROTOCOL, BOOLEAN) -> EFI_STATUS
    OutputString:(@EFI_SIMPLE_TEXT_OUTPUT_PROTOCOL, @CHAR16) -> EFI_STATUS
```

TypeScript-like signature syntax. Assigned with `&`:
```
compare: (@Node, @Node) -> int = &my_compare_fn
```

### Implicit Self
```
# LowPy source:
SystemTable.ConOut.Reset(true)

# Compiler rewrites to (at IR emit stage):
Reset(SystemTable.ConOut, true)
```

The first argument of a function pointer field is always the implicit receiver.

### Wide Strings (UTF-16LE)
```
SystemTable.ConOut.OutputString(u"Hello UEFI!\r\n")
```

`u""` prefix = UTF-16LE encoding, 2 bytes per char, `0x0000` null terminator. Maps to `CHAR16*` in UEFI.

In QBE IR:
```
data $wstr = { h 72, h 101, h 108, h 108, h 111, h 0 }
```

### Memory Layout Directives
```
type Packet:
    header: u8
    length: u16
    data:   @u8
    __layout__(packed, alignment=4)
```

For network packets, hardware registers, UEFI structures.

### C Header Imports
```
import "stdio.h" as stdio
```

### Inline Assembly
```
asm:
    mov rax, 0x1
    syscall
```

Core, non-optional requirement. Deferred in current implementation.

### Booleans
```
true
false
```

### Built-in Numeric Types
`u8`, `u16`, `u32`, `u64`, `i8`, `i16`, `i32`, `i64`

---

## Roadmap

### Phase 1 — libc-dependent
- Static allocation, stack only
- Full lexer ✅ (~90% complete)
- Recursive descent parser 🚧
- AST node classes 🚧
- QBE IR emission
- Basic UEFI hello world compiling end-to-end

### Phase 2 — Optional runtime
- Arena GC (opt-in)
- `comptime` — Zig-inspired compile-time execution, replaces macros
- Shares tree-walking interpreter with the parser

### Phase 3 — Freestanding
- Own libc
- Direct syscalls
- No external dependencies

---

## UEFI Example

```python
type EFI_SIMPLE_TEXT_OUTPUT_PROTOCOL:
    Reset:(@EFI_SIMPLE_TEXT_OUTPUT_PROTOCOL, BOOLEAN) -> EFI_STATUS
    OutputString:(@EFI_SIMPLE_TEXT_OUTPUT_PROTOCOL, @CHAR16) -> EFI_STATUS

type EFI_SYSTEM_TABLE:
    hrd:              EFI_TABLE_HEADER
    FirmwareVendor:   @CHAR16
    FirmwareVersion:  UINT32
    ConsoleInHandle:  EFI_HANDLE
    ConIn:            @EFI_SIMPLE_TEXT_INPUT_PROTOCOL
    ConsoleOutHandle: EFI_HANDLE
    ConOut:           @EFI_SIMPLE_TEXT_OUTPUT_PROTOCOL

def efi_main(ImageHandle: EFI_HANDLE, SystemTable: @EFI_SYSTEM_TABLE) -> EFI_STATUS:
    SystemTable.ConOut.Reset(true)
    SystemTable.ConOut.OutputString(u"Testing...\r\n")
    while true:
        pass
    return 0
```

---

## Project Structure

```
lowpy-python/
├── lexer/
│   ├── lexer.py         # Main lexer
│   ├── tokens.py        # TokenType definitions
│   └── keywords.py      # All reserved keywords
├── tests/
│   └── lexer/
│       └── uefi_example.lpy
└── README.md
```

---

## Why QBE and not LLVM?

LLVM is a dependency you have to fight. QBE is ~10k lines of C, readable, hackable, and produces good code for x86-64 and ARM64. For a language targeting UEFI and OS development, QBE's simplicity is a feature. MS x64 ABI (`winabi`) is supported for UEFI targets.

---

## Status

Early development. Lexer ~90% complete. Parser and AST in progress.

Not ready for use. Design is being locked down as implementation progresses.