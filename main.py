import argparse
import os
import json
from concurrent.futures import ThreadPoolExecutor
from src.lexer import Lexer, TokenType

BASE_TEST_DIR = os.path.join(os.path.dirname(__file__), "tests")

def gather_test_files(test_dir):
    if os.path.exists(test_dir) and os.path.isdir(test_dir):
        return [os.path.join(test_dir,f) for f in os.listdir(test_dir) if f.endswith(".lpy")]
    return []

def process_file(path, generate=False, generate_text=False):
    with open(path, "r") as f:
        code = f.read()
    lexer = Lexer(code)
    tokens = list(lexer)
    if generate:
        token_dict = [tok.to_dict() for tok in tokens]
        output_file_path = path + ".snap"
        with open(output_file_path, "w") as exp_file:
            json.dump(token_dict, exp_file, indent=4)
    if generate_text:
        output_file_path = path + ".txt"
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
    return path, tokens




def main():
    parser = argparse.ArgumentParser(description='LowPy language tool')

    parser.add_argument('-f', '--file', help='source .lpy file',required=False,default=None)

    parser.add_argument('-g','--generate',help='generate expected output for a test file', action='store_true', required=False, default=False)
    
    parser.add_argument('-gt','--generate-text',help='generate expected output as text for a test file', action='store_true', required=False, default=False)

    parser.add_argument('-j', '--jobs', type=int, default=4, help='number of threads for parallel processing (default: 4)', required=False)

    parser.add_argument('-t', '--test', choices=['lexer', 'parser'],               # shorthand + longhand
                        help='run tests for lexer or parser', required=True)
    parser.add_argument('-o', '--output', default='stdout',                        # assignable with default
                        help='output destination (default: stdout)', required=False)
    parser.add_argument('-v', '--verbose', action='store_true',                    # flag (true/false)
                        help='verbose output', required=False)
    args = parser.parse_args()
        
    print(f"Running {args.test} tests with file={args.file}, generate={args.generate}, jobs={args.jobs}, output={args.output}, verbose={args.verbose}, generate_text={args.generate_text}")
    if args.test == "lexer":
        if args.file is None:
            test_files = gather_test_files(os.path.join(BASE_TEST_DIR, "lexer"))
        else:
            test_files = [args.file] if os.path.exists(args.file) else []
        
        if not test_files:
            print(f"No .lpy files found in {BASE_TEST_DIR} or specified file {args.file} does not exist.")
            return
        
        print(f"Processing files: {test_files}")
        with ThreadPoolExecutor(max_workers=args.jobs) as executor:
            results = list(executor.map(lambda f: process_file(f, args.generate, args.generate_text), test_files))
            
        
        if args.verbose:
            for path, tokens in results:
                print(f"\n=== Tokens for file: {path} ===")
                indent = 0
                for tok in tokens:
                    match tok.type:
                        case TokenType.INDENT:
                            print("    " * indent,"{" )
                            indent += 1
                        case TokenType.DEDENT:
                            indent -= 1
                            print("    " * indent,"}" ) 
                        case TokenType.NEWLINE:
                            print("")
                        case _:
                            print("    " * indent + repr(tok), end="")
                print("")
        if args.generate:
           print(f"following expected output files generated: {[f+'.snap' for f in test_files]}")
        if args.generate_text:
            print(f"following expected text files generated: {[f+'.txt' for f in test_files]}")
        elif args.test == "parser":
            print("Parser tests not implemented yet")
if __name__ == "__main__":
    main()