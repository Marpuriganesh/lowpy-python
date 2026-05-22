import argparse
import os
import json
from concurrent.futures import ThreadPoolExecutor
from src.lexer import Lexer, TokenType
from enum import Enum, auto
from src.parser import Parser

from rich.console import Console
from rich.table import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)
from rich.panel import Panel

# from rich import print as rprint
from rich.text import Text
# from rich.rule import Rule
from rich import box

console = Console()


class TestType(Enum):
    lexer = auto()
    parser = auto()


BASE_TEST_DIR = os.path.join(os.path.dirname(__file__), "tests")


def gather_test_files(test_dir):
    if os.path.exists(test_dir) and os.path.isdir(test_dir):
        return [
            os.path.join(test_dir, f)
            for f in os.listdir(test_dir)
            if f.endswith(".lpy")
        ]
    return []


def assert_snap(actual, snap_path):
    if not os.path.exists(snap_path):
        return False, f"Snapshot file not found: {snap_path}"
    with open(snap_path, "r") as snap_file:
        expected = json.load(snap_file)
    passed = True
    error_messages = []
    max_len = max(len(expected), len(actual))

    for i in range(max_len):
        if i >= len(expected):
            # print(f"Extra token at {i}")
            # print("Got:", actual[i])
            passed = False
            error_message = f"Extra token at {i}:\n Got {actual[i]}"
            error_messages.append(error_message)
            break

        if i >= len(actual):
            print(f"Missing token at {i}")
            print("Expected:", expected[i])
            passed = False
            error_message = f"Missing token at {i}:\n Expected {expected[i]}"
            error_messages.append(error_message)
            break

        exp = expected[i]
        got = actual[i]

        if exp != got:
            # print(f"Mismatch at token {i}")
            # print("Expected:", exp)
            # print("Got     :", got)
            passed = False
            error_message = f"Mismatch at token {i}:\n Expected: {exp}\n Got: {got}"
            error_messages.append(error_message)

    return passed, error_messages


def assert_file(
    file_path,
    test_type: TestType = TestType.lexer,
):
    Passed = {
        "lexer": None,
        "parser": None,
    }
    ErrorMessages = {
        "lexer": None,
        "parser": None,
    }
    base_folder_name = os.path.splitext(os.path.basename(file_path))[0]
    with open(file_path, "r") as f:
        code = f.read()
    lexer = Lexer(code)
    tokens = list(lexer)
    ast_as_list = []
    console.print(f"asserting {os.path.basename(file_path)}...")
    token_dict = [tok.to_dict() for tok in tokens]
    snap_path = os.path.join(
        os.path.dirname(file_path),
        base_folder_name,
        base_folder_name + "_lex",
        os.path.basename(file_path) + ".lex.snap",
    )
    lex_passed, lex_error_messages = assert_snap(token_dict, snap_path)
    Passed["lexer"] = lex_passed
    ErrorMessages["lexer"] = lex_error_messages
    if test_type == TestType.parser:
        parser = Parser(tokens)
        try:
            result = parser.parse()
            ast_as_list = (
                [node.to_dict() for node in result] if result is not None else []
            )
            snap_path = os.path.join(
                os.path.dirname(file_path),
                base_folder_name,
                base_folder_name + "_ast",
                os.path.basename(file_path) + ".ast.snap",
            )
            ast_passed, ast_error_messages = assert_snap(ast_as_list, snap_path)
            Passed["parser"] = ast_passed
            ErrorMessages["parser"] = ast_error_messages
        except Exception as e:
            expected_error_path = os.path.join(
                os.path.dirname(file_path),
                base_folder_name,
                base_folder_name + "_ast",
                os.path.basename(file_path) + ".ast.error",
            )
            if os.path.exists(expected_error_path):
                with open(expected_error_path, "r") as ef:
                    lines = ef.read().splitlines()
                # strip the === header, "Error occurred while parsing..." line, and === footer
                lines = [line for line in lines if not line.startswith("=") and not line.startswith("Error occurred while parsing")]
                expected_error = "\n".join(lines).strip()
                actual_error = str(e).strip()
                if expected_error in actual_error:
                    Passed["parser"] = True
                    ErrorMessages["parser"] = []
                else:
                    Passed["parser"] = False
                    ErrorMessages["parser"] = [
                        f"Expected error mismatch:\n Expected: {expected_error}\n Got: {actual_error}"
                    ]
            else:
                Passed["parser"] = False
                ErrorMessages["parser"] = [str(e)]
    return file_path, Passed, ErrorMessages


def process_file(
    file_path,
    generate=False,
    generate_text=False,
    test_type: TestType = TestType.lexer,
):
    file_errored = False
    error_message = None
    base_folder_name = os.path.splitext(os.path.basename(file_path))[0]
    with open(file_path, "r") as f:
        code = f.read()
    lexer = Lexer(code)
    tokens = list(lexer)
    ast_as_list = []

    if generate:
        token_dict = [tok.to_dict() for tok in tokens]
        base_folder_path = os.path.join(os.path.dirname(file_path), base_folder_name)
        os.makedirs(base_folder_path, exist_ok=True)
        folder_name = base_folder_name + "_lex"
        folder_path = os.path.join(base_folder_path, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        output_file_path = os.path.join(
            folder_path, os.path.basename(file_path) + ".lex.snap"
        )
        with open(output_file_path, "w") as exp_file:
            json.dump(token_dict, exp_file, indent=4)

    if generate_text:
        base_folder_path = os.path.join(os.path.dirname(file_path), base_folder_name)
        os.makedirs(base_folder_path, exist_ok=True)
        folder_name = base_folder_name + "_lex"
        folder_path = os.path.join(base_folder_path, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        output_file_path = os.path.join(
            folder_path, os.path.basename(file_path) + ".lex.txt"
        )
        indent = 0
        with open(output_file_path, "w") as exp_file:
            for tok in tokens:
                match tok.type:
                    case TokenType.INDENT:
                        exp_file.write("    " * indent + "{\n")
                        indent += 1
                    case TokenType.DEDENT:
                        indent -= 1
                        exp_file.write("    " * indent + "}\n")
                    case TokenType.NEWLINE:
                        exp_file.write("\n")
                    case _:
                        exp_file.write("    " * indent + repr(tok))
            exp_file.write("\n")

    if test_type == TestType.parser:
        parser = Parser(tokens)
        try:
            result = parser.parse()
            ast_as_list = (
                [node.to_dict() for node in result] if result is not None else []
            )
            if generate:
                base_folder_path = os.path.join(
                    os.path.dirname(file_path), base_folder_name
                )
                os.makedirs(base_folder_path, exist_ok=True)
                folder_name = base_folder_name + "_ast"
                folder_path = os.path.join(base_folder_path, folder_name)
                os.makedirs(folder_path, exist_ok=True)
                with open(
                    os.path.join(
                        folder_path, os.path.basename(file_path) + ".ast.snap"
                    ),
                    "w",
                ) as ast_file:
                    json.dump(ast_as_list, ast_file, indent=4)
            if generate_text:
                base_folder_path = os.path.join(
                    os.path.dirname(file_path), base_folder_name
                )
                os.makedirs(base_folder_path, exist_ok=True)
                folder_name = base_folder_name + "_ast"
                folder_path = os.path.join(base_folder_path, folder_name)
                os.makedirs(folder_path, exist_ok=True)
                with open(
                    os.path.join(folder_path, os.path.basename(file_path) + ".ast.txt"),
                    "w",
                ) as ast_text_file:
                    for node in result:
                        ast_text_file.write(f"{node}\n")
        except Exception as e:
            file_errored = True
            error_message = str(e)
            exception_string = (
                "=" * 30
                + " Parsing error "
                + "=" * 30
                + "\n"
                + f"Error occurred while parsing {file_path}{e}\n"
                + "=" * 75
            )
            base_folder_path = os.path.join(
                os.path.dirname(file_path), base_folder_name
            )
            os.makedirs(base_folder_path, exist_ok=True)
            folder_name = base_folder_name + "_ast"
            folder_path = os.path.join(base_folder_path, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            with open(
                os.path.join(folder_path, os.path.basename(file_path) + ".ast.error"),
                "w",
            ) as error_file:
                error_file.write(exception_string)

    return file_path, tokens, ast_as_list, file_errored, error_message


def print_generate_summary(results, test_type, generate, generate_text):
    """Rich summary table for generate mode."""
    console.print()
    console.rule("[bold yellow]Generate Results[/bold yellow]")
    console.print()

    table = Table(
        show_header=True,
        header_style="bold cyan",
        border_style="dim white",
        expand=True,
    )
    table.add_column("File", style="white", no_wrap=False)
    table.add_column("Tokens", justify="right", style="dim cyan")
    table.add_column("AST Nodes", justify="right", style="dim magenta")
    table.add_column("Status", justify="center")
    table.add_column("Error", style="red", no_wrap=False)

    passed = 0
    failed = 0

    for file_path, tokens, ast_list, errored, error_msg in results:
        fname = os.path.basename(file_path)
        token_count = str(len(tokens))
        ast_count = str(len(ast_list)) if test_type == TestType.parser else "—"

        if errored:
            failed += 1
            status = Text("✗ ERROR", style="bold red")
            # show first line of error only — full error is in .ast.error file
            short_error = (error_msg or "").splitlines()[0][:80] if error_msg else ""
            table.add_row(fname, token_count, ast_count, status, short_error)
        else:
            passed += 1
            status = Text("✓ OK", style="bold green")
            table.add_row(fname, token_count, ast_count, status, "")

    console.print(table)
    console.print()

    # summary line
    summary = Text()
    summary.append(f"  {passed} generated", style="bold green")
    summary.append("  •  ", style="dim")
    summary.append(f"{failed} failed", style="bold red" if failed else "dim")
    console.print(
        Panel(
            summary,
            title="[bold]Summary[/bold]",
            border_style="dim white",
            padding=(0, 2),
        )
    )

    # output file hints
    if generate or generate_text:
        console.print()
        hints = []
        if generate:
            hints.append(
                "  [dim]Snap files:[/dim] [cyan].lex.snap[/cyan] / [magenta].ast.snap[/magenta]"
            )
        if generate_text:
            hints.append(
                "  [dim]Text files:[/dim] [cyan].lex.txt[/cyan] / [magenta].ast.txt[/magenta]"
            )
        if failed:
            hints.append("  [dim]Error files:[/dim] [red].ast.error[/red]")
        for h in hints:
            console.print(h)
    console.print()


def _parse_diff(error_msg: str):
    """Extract (expected, got) strings from an error message."""
    try:
        if "\n Expected: " in error_msg and "\n Got: " in error_msg:
            after_exp = error_msg.split("\n Expected: ", 1)[1]
            expected, got = after_exp.split("\n Got: ", 1)
            return expected.strip(), got.strip()
    except Exception:
        pass
    return None, None


def _render_diff_table(error_messages: list):
    for msg in error_messages:
        header_line = msg.split("\n")[0].strip()
        expected, got = _parse_diff(msg)

        console.print(f"    [dim]·[/dim] [white]{header_line}[/white]")

        if expected is not None and got is not None:
            diff = Table(
                box=box.SIMPLE,
                show_header=True,
                header_style="bold",
                padding=(0, 2),
                expand=False,
            )
            diff.add_column("Expected", style="green", no_wrap=False, min_width=40)
            diff.add_column("Got", style="red", no_wrap=False, min_width=40)
            diff.add_row(expected, got)
            console.print(diff)
        else:
            for line in msg.splitlines():
                console.print(f"      [dim]{line}[/dim]")
        console.print()


def print_assert_summary(results, test_type):
    import time

    is_parser = test_type.name == "parser"
    start = time.perf_counter()

    console.print()
    console.rule(
        f"[bold] LowPy [yellow]{test_type.name.upper()}[/yellow] — ASSERT [/bold]"
    )
    console.print()

    # ── Compact table ──────────────────────────────────────────────────────────
    table = Table(
        box=box.SIMPLE, show_header=False, padding=(0, 1), expand=False, show_edge=False
    )
    table.add_column("status", width=3)
    table.add_column("file", style="white", no_wrap=True)
    table.add_column("lex", justify="right", no_wrap=True)
    table.add_column("ast", justify="right", no_wrap=True)
    table.add_column("tag", no_wrap=True)

    failed_files = []
    total_pass = 0
    total_fail = 0

    for file_path, res, err in results:
        fname = os.path.basename(file_path)
        lex_ok = bool(res["lexer"])
        ast_ok = bool(res["parser"]) if is_parser else True
        overall_ok = lex_ok and ast_ok

        if overall_ok:
            total_pass += 1
            icon = Text("✓", style="bold green")
            fname_text = Text(fname, style="green")
            tag = Text("")
        else:
            total_fail += 1
            icon = Text("✗", style="bold red")
            fname_text = Text(fname, style="red")
            failed_parts = []
            if not lex_ok:
                failed_parts.append("lexer")
            if is_parser and not ast_ok:
                failed_parts.append("parser")
            tag = Text(" › ".join(failed_parts), style="dim red")
            failed_files.append((file_path, fname, res, err))

        lex_badge = (
            Text("lex ✓", style="dim green")
            if lex_ok
            else Text("lex ✗", style="dim red")
        )
        ast_badge = (
            (
                Text("ast ✓", style="dim green")
                if ast_ok
                else Text("ast ✗", style="dim red")
            )
            if is_parser
            else Text("—", style="dim")
        )

        table.add_row(icon, fname_text, lex_badge, ast_badge, tag)

    console.print(table)

    # ── Failure details ────────────────────────────────────────────────────────
    if failed_files:
        console.print()
        console.rule("[bold red] FAILURES [/bold red]")

        for _, fname, res, err in failed_files:
            lex_ok = bool(res["lexer"])
            ast_ok = bool(res["parser"]) if is_parser else True

            if not lex_ok and err.get("lexer"):
                console.print()
                console.print(
                    f"  [bold red]FAIL[/bold red] [white]{fname}[/white] [dim]›[/dim] [yellow]lexer[/yellow]"
                )
                console.print()
                _render_diff_table(err["lexer"])

            if is_parser and not ast_ok and err.get("parser"):
                console.print()
                console.print(
                    f"  [bold red]FAIL[/bold red] [white]{fname}[/white] [dim]›[/dim] [yellow]parser[/yellow]"
                )
                console.print()
                _render_diff_table(err["parser"])

    # ── Footer ─────────────────────────────────────────────────────────────────
    elapsed = time.perf_counter() - start
    total = total_pass + total_fail

    console.print()
    console.rule("[dim]─[/dim]")

    def _summary_line(label, fail, passed, tot):
        t = Text(f"  {label}:  ")
        if fail:
            t.append(f"{fail} failed", style="bold red")
            t.append("  |  ", style="dim")
        t.append(f"{passed} passed", style="bold green")
        t.append("  |  ", style="dim")
        t.append(f"{tot} total", style="white")
        return t

    console.print(_summary_line("Test Suites", total_fail, total_pass, total))
    console.print(_summary_line("Tests      ", total_fail, total_pass, total))
    console.print(f"  [dim]Time:[/dim]        [white]{elapsed:.3f}s[/white]")
    console.print()


def main():
    parser = argparse.ArgumentParser(description="LowPy language tool")

    parser.add_argument(
        "-f", "--file", help="source .lpy file", required=False, default=None
    )
    parser.add_argument(
        "-g",
        "--generate",
        help="generate expected output",
        action="store_true",
        required=False,
        default=False,
    )
    parser.add_argument(
        "-gt",
        "--generate-text",
        help="generate expected output as text",
        action="store_true",
        required=False,
        default=False,
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=4,
        help="parallel threads (default: 4)",
        required=False,
    )
    parser.add_argument(
        "-t",
        "--test",
        choices=["lexer", "parser"],
        help="run tests for lexer or parser",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output",
        default="stdout",
        help="output destination (default: stdout)",
        required=False,
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="verbose output", required=False
    )

    args = parser.parse_args()

    test_type = TestType.lexer if args.test == "lexer" else TestType.parser
    mode = "generate" if (args.generate or args.generate_text) else "assert"

    # header
    console.print()
    console.rule(
        f"[bold]LowPy [yellow]{args.test.upper()}[/yellow] — {mode.upper()} MODE[/bold]"
    )
    meta = Table.grid(padding=(0, 2))
    meta.add_column(style="dim")
    meta.add_column(style="white")
    meta.add_row("file", args.file or "all")
    meta.add_row("jobs", str(args.jobs))
    meta.add_row("generate snap", "yes" if args.generate else "no")
    meta.add_row("generate text", "yes" if args.generate_text else "no")
    meta.add_row("verbose", "yes" if args.verbose else "no")
    console.print(meta)
    console.print()

    if args.file is None:
        dir_key = "lexer" if test_type == TestType.lexer else "parser"
        test_files = gather_test_files(os.path.join(BASE_TEST_DIR, dir_key))
    else:
        test_files = [args.file] if os.path.exists(args.file) else []

    if not test_files:
        console.print("[red]No .lpy files found.[/red]")
        return

    console.print(f"[dim]Found {len(test_files)} file(s):[/dim]")
    for f in test_files:
        console.print(f"  [dim cyan]{os.path.basename(f)}[/dim cyan]")
    console.print()

    if mode == "generate":
        results = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("[cyan]Processing...", total=len(test_files))

            with ThreadPoolExecutor(max_workers=args.jobs) as executor:
                futures = {
                    executor.submit(
                        process_file, f, args.generate, args.generate_text, test_type
                    ): f
                    for f in test_files
                }
                for future in futures:
                    result = future.result()
                    results.append(result)
                    progress.advance(task)
    else:
        results = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("[cyan]Asserting...", total=len(test_files))

            with ThreadPoolExecutor(max_workers=args.jobs) as executor:
                futures = {
                    executor.submit(assert_file, f, test_type): f for f in test_files
                }
                for future in futures:
                    result = future.result()
                    results.append(result)
                    progress.advance(task)

    if mode == "generate":
        print_generate_summary(results, test_type, args.generate, args.generate_text)
    else:
        print_assert_summary(results, test_type)

    if args.verbose:
        console.print()
        console.rule("[dim]Verbose Token Output[/dim]")
        for file_path, tokens, ast_list, _, _ in results:
            console.print(f"\n[bold]{os.path.basename(file_path)}[/bold]")
            indent = 0
            for tok in tokens:
                match tok.type:
                    case TokenType.INDENT:
                        console.print("    " * indent + "{", style="dim")
                        indent += 1
                    case TokenType.DEDENT:
                        indent -= 1
                        console.print("    " * indent + "}", style="dim")
                    case TokenType.NEWLINE:
                        console.print("")
                    case _:
                        console.print("    " * indent + repr(tok), end="")
            for ast_node in ast_list:
                console.print(f"\n[magenta]AST:[/magenta] {ast_node}")


if __name__ == "__main__":
    main()
