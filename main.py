import sys
from lexer import Lexer
from parser import Parser
from interpreter import Interpreter

def main():
    # Read input from file, stdin, or argument
    if len(sys.argv) > 1:
        # Read from file
        filename = sys.argv[1]
        with open(filename, 'r') as f:
            code = f.read()
    else:
        # Read from stdin
        code = sys.stdin.read()
    
    try:
        # Lexical analysis
        tokens = Lexer(code).tokenize()
        
        # Parsing
        parser = Parser(tokens)
        tree = parser.parse()
        
        # Interpretation
        interpreter = Interpreter()
        interpreter.interpret(tree)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()