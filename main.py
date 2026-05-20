import argparse
import os
import json
from concurrent.futures import ThreadPoolExecutor
from src.lexer import Lexer, TokenType
from enum import Enum, auto
from src.parser import Parser


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


def process_file(
    path,
    generate=False,
    generate_text=False,
    test_type: TestType = TestType.lexer,
):
    file_errored = False
    base_folder_name = os.path.splitext(os.path.basename(path))[0]  # → "var_err_empty_generic"
    with open(path, "r") as f:
        code = f.read()
    lexer = Lexer(code)
    tokens = list(lexer)
    ast_as_list = []
    if generate:
        token_dict = [tok.to_dict() for tok in tokens]
        base_folder_path = os.path.join(os.path.dirname(path), base_folder_name)
        os.makedirs(base_folder_path, exist_ok=True)
        folder_name = base_folder_name+"_lex"
        folder_path = os.path.join(base_folder_path, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        output_file_path = os.path.join(folder_path, os.path.basename(path) + ".lex.snap")
        with open(output_file_path, "w") as exp_file:
            json.dump(token_dict, exp_file, indent=4)
    if generate_text:
        base_folder_path = os.path.join(os.path.dirname(path), base_folder_name)
        os.makedirs(base_folder_path, exist_ok=True)
        folder_name = base_folder_name+"_lex"
        folder_path = os.path.join(base_folder_path, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        output_file_path = os.path.join(folder_path, os.path.basename(path) + ".lex.txt")
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
                folder_name = base_folder_name+"_ast"
                folder_path = os.path.join(base_folder_path, folder_name)
                os.makedirs(folder_path, exist_ok=True)
                with open(os.path.join(folder_path, os.path.basename(path) + ".ast.snap"), "w") as ast_file:
                    json.dump(ast_as_list, ast_file, indent=4)
            if generate_text:
                base_folder_path = os.path.join(os.path.dirname(path), base_folder_name)
                os.makedirs(base_folder_path, exist_ok=True)
                folder_name = base_folder_name+"_ast"
                folder_path = os.path.join(base_folder_path, folder_name)
                os.makedirs(folder_path, exist_ok=True)
                with open(os.path.join(folder_path, os.path.basename(path) + ".ast.txt"), "w") as ast_text_file:
                    for node in result:
                        ast_text_file.write(f"{node}\n")
        except Exception as e:
            file_errored = True
            exception_string = "=" * 30 + " Parsing error " + "=" * 30 + "\n"+f"Error occurred while parsing {path}{e}\n"+"=" * 75
            print(exception_string)
            base_folder_path = os.path.join(os.path.dirname(path), base_folder_name)
            os.makedirs(base_folder_path, exist_ok=True)
            folder_name = base_folder_name+"_ast"
            folder_path = os.path.join(base_folder_path, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            with open(os.path.join(folder_path, os.path.basename(path) + ".ast.error"), "w") as error_file:
                error_file.write(exception_string)
        if not file_errored:
            print("###"*10+f" Finished processing {path} "+"###"*10+"\n")
    return path, tokens, ast_as_list


def main():
    parser = argparse.ArgumentParser(description="LowPy language tool")

    parser.add_argument(
        "-f", "--file", help="source .lpy file", required=False, default=None
    )

    parser.add_argument(
        "-g",
        "--generate",
        help="generate expected output for a test file",
        action="store_true",
        required=False,
        default=False,
    )

    parser.add_argument(
        "-gt",
        "--generate-text",
        help="generate expected output as text for a test file",
        action="store_true",
        required=False,
        default=False,
    )

    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=4,
        help="number of threads for parallel processing (default: 4)",
        required=False,
    )

    parser.add_argument(
        "-t",
        "--test",
        choices=["lexer", "parser"],  # shorthand + longhand
        help="run tests for lexer or parser",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output",
        default="stdout",  # assignable with default
        help="output destination (default: stdout)",
        required=False,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",  # flag (true/false)
        help="verbose output",
        required=False,
    )
    args = parser.parse_args()

    print(
        f"Running {args.test} tests with file={args.file}, generate={args.generate}, jobs={args.jobs}, output={args.output}, verbose={args.verbose}, generate_text={args.generate_text}\n"+"+"*75
    )
    test_type = TestType.lexer if args.test == "lexer" else TestType.parser

    if args.file is None:
        test_files = gather_test_files(os.path.join(BASE_TEST_DIR, "lexer")) if test_type == TestType.lexer else gather_test_files(os.path.join(BASE_TEST_DIR, "parser"))
    else:
        test_files = [args.file] if os.path.exists(args.file) else []

    if not test_files:
        print(
            f"No .lpy files found in {BASE_TEST_DIR} or specified file {args.file} does not exist."
        )
        return

    print(f"\n### Processing files: {test_files}\n")
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        results = list(
            executor.map(
                lambda f: process_file(f, args.generate, args.generate_text, test_type),
                test_files,
            )
        )

    if args.verbose:
        for path, tokens, ast_list in results:
            print(f"\n=== Tokens for file: {path} ===")
            indent = 0
            for tok in tokens:
                match tok.type:
                    case TokenType.INDENT:
                        print("    " * indent, "{")
                        indent += 1
                    case TokenType.DEDENT:
                        indent -= 1
                        print("    " * indent, "}")
                    case TokenType.NEWLINE:
                        print("")
                    case _:
                        print("    " * indent + repr(tok), end="")
            for ast_node in ast_list:
                print(f"\nAST Node: {ast_node}")
            print("")
    if args.generate:
        print(
            f"following expected output files generated:\n {[f + '.lex.snap' for f in test_files]}\n"
        )
    if args.generate_text:
        print(
            f"following expected text files generated:\n {[f + '.lex.txt' for f in test_files]}"
        )


if __name__ == "__main__":
    main()
