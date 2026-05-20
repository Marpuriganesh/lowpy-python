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


def assert_file(
    path,test_type: TestType = TestType.lexer
):
    # placeholder for assert mode — will compare generated output to expected .snap files
    pass


def process_file(
    path,
    generate=False,
    generate_text=False,
    test_type: TestType = TestType.lexer,
):
    file_errored = False
    error_message = None
    base_folder_name = os.path.splitext(os.path.basename(path))[0]
    with open(path, "r") as f:
        code = f.read()
    lexer = Lexer(code)
    tokens = list(lexer)
    ast_as_list = []

    if generate:
        token_dict = [tok.to_dict() for tok in tokens]
        base_folder_path = os.path.join(os.path.dirname(path), base_folder_name)
        os.makedirs(base_folder_path, exist_ok=True)
        folder_name = base_folder_name + "_lex"
        folder_path = os.path.join(base_folder_path, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        output_file_path = os.path.join(
            folder_path, os.path.basename(path) + ".lex.snap"
        )
        with open(output_file_path, "w") as exp_file:
            json.dump(token_dict, exp_file, indent=4)

    if generate_text:
        base_folder_path = os.path.join(os.path.dirname(path), base_folder_name)
        os.makedirs(base_folder_path, exist_ok=True)
        folder_name = base_folder_name + "_lex"
        folder_path = os.path.join(base_folder_path, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        output_file_path = os.path.join(
            folder_path, os.path.basename(path) + ".lex.txt"
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
                base_folder_path = os.path.join(os.path.dirname(path), base_folder_name)
                os.makedirs(base_folder_path, exist_ok=True)
                folder_name = base_folder_name + "_ast"
                folder_path = os.path.join(base_folder_path, folder_name)
                os.makedirs(folder_path, exist_ok=True)
                with open(
                    os.path.join(folder_path, os.path.basename(path) + ".ast.snap"), "w"
                ) as ast_file:
                    json.dump(ast_as_list, ast_file, indent=4)
            if generate_text:
                base_folder_path = os.path.join(os.path.dirname(path), base_folder_name)
                os.makedirs(base_folder_path, exist_ok=True)
                folder_name = base_folder_name + "_ast"
                folder_path = os.path.join(base_folder_path, folder_name)
                os.makedirs(folder_path, exist_ok=True)
                with open(
                    os.path.join(folder_path, os.path.basename(path) + ".ast.txt"), "w"
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
                + f"Error occurred while parsing {path}{e}\n"
                + "=" * 75
            )
            base_folder_path = os.path.join(os.path.dirname(path), base_folder_name)
            os.makedirs(base_folder_path, exist_ok=True)
            folder_name = base_folder_name + "_ast"
            folder_path = os.path.join(base_folder_path, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            with open(
                os.path.join(folder_path, os.path.basename(path) + ".ast.error"), "w"
            ) as error_file:
                error_file.write(exception_string)

    return path, tokens, ast_as_list, file_errored, error_message


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

    for path, tokens, ast_list, errored, error_msg in results:
        fname = os.path.basename(path)
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


def print_assert_summary(results, test_type):
    """Placeholder — will be filled when assert mode is built."""
    console.print()
    console.rule("[bold blue]Assert Results[/bold blue]")
    console.print("  [dim]Assert mode not yet implemented.[/dim]")
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

    if mode == "generate":
        print_generate_summary(results, test_type, args.generate, args.generate_text)
    else:
        print_assert_summary(results, test_type)

    if args.verbose:
        console.print()
        console.rule("[dim]Verbose Token Output[/dim]")
        for path, tokens, ast_list, _, _ in results:
            console.print(f"\n[bold]{os.path.basename(path)}[/bold]")
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
