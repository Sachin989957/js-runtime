# JavaScript Runtime - Thunder Hackathon 2.0

A complete JavaScript interpreter written in Python that can execute JavaScript code. This runtime implements a lexer, parser, and interpreter to support core JavaScript features.

## Features Supported

### Data Types
- **Primitives**: `number`, `string`, `boolean`, `null`, `undefined`
- **Objects**: Arrays, Objects
- **Functions**: Function declarations, function expressions, arrow functions

### Operators
- **Arithmetic**: `+`, `-`, `*`, `/`, `%`, `**` (exponentiation)
- **Comparison**: `==`, `!=`, `===`, `!==`, `<`, `>`, `<=`, `>=`
- **Logical**: `&&`, `||`, `!`
- **Bitwise**: `&`, `|`, `^`, `~`
- **Assignment**: `=`, `+=`, `-=`, `*=`, `/=`, `%=`
- **Unary**: `++`, `--`, `-`, `+`, `!`, `typeof`
- **Ternary**: `condition ? true_expr : false_expr`

### Control Flow
- **Conditionals**: `if`, `else if`, `else`
- **Loops**: `for`, `while`, `do...while`
- **Jump**: `break`, `continue`, `return`

### Variables
- `let` and `const` declarations with block scoping
- Proper variable scope handling

### Functions
- Function declarations: `function name(params) { }`
- Function expressions: `const fn = function(params) { }`
- Callback functions support
- Closures and lexical scoping

### Array Methods
- `push()`, `pop()`, `shift()`, `unshift()`
- `slice()`, `splice()`, `concat()`
- `indexOf()`, `includes()`, `join()`
- `reverse()`, `sort()`
- `map()`, `filter()`, `reduce()`
- `find()`, `some()`, `every()`
- Spread operator `...` for array unpacking

### String Methods
- `split()`, `replace()`, `replaceAll()`
- `substring()`, `slice()`, `trim()`
- `toUpperCase()`, `toLowerCase()`
- `includes()`, `startsWith()`, `endsWith()`
- `indexOf()`, `charAt()`
- String concatenation with `+`

### Built-in Objects
- **Math**: `Math.floor()`, `Math.ceil()`, `Math.round()`, `Math.abs()`, `Math.sqrt()`, `Math.pow()`, `Math.random()`, `Math.PI`, `Math.E`
- **Console**: `console.log()`
- **Date**: Basic `Date` object support
- **Array**: Array constructor

### Other Features
- Type coercion and conversions
- Truthy/falsy evaluation
- Object literals and property access
- Array indexing

## Installation

### Requirements
- Python 3.7 or higher

### Setup
```bash
# No additional dependencies required
# The runtime uses only Python's built-in libraries
```

## Usage

### Running from a File
```bash
python main.py path/to/script.js
```

### Running from stdin
```bash
echo 'console.log("Hello, World!");' | python main.py
```

### Example
```bash
$ echo 'let arr = [1, 2, 3]; console.log(arr.map(x => x * 2));' | python main.py
2,4,6
```

## Test Cases

The runtime has been tested against the following JavaScript programs:

### Test 1: Odd/Even Checker
```javascript
let num = 7;
if (num % 2 === 0) {
    console.log(num + " is Even");
} else {
    console.log(num + " is Odd");
}
// Output: 7 is Odd
```

### Test 2: Triangle Pattern
```javascript
for (let i = 1; i <= 5; i++) {
    let row = "";
    for (let j = 1; j <= i; j++) {
        row += "*";
    }
    console.log(row);
}
// Output:
// *
// **
// ***
// ****
// *****
```

### Test 3: Armstrong Number Checker
```javascript
function isArmstrong(num) {
    let temp = num;
    let sum = 0;
    while (temp > 0) {
        let digit = temp % 10;
        sum += digit ** 3;
        temp = Math.floor(temp / 10);
    }
    return sum === num;
}
console.log(isArmstrong(153));  // Output: true
console.log(isArmstrong(123));  // Output: false
```

### Test 4: Array Reverse
```javascript
let arr = [1, 2, 3, 4, 5];
let reversed = [...arr].reverse();
console.log("Original: " + arr.join(", "));
console.log("Reversed: " + reversed.join(", "));
// Output:
// Original: 1, 2, 3, 4, 5
// Reversed: 5, 4, 3, 2, 1
```

### Test 5: Palindrome Checker
```javascript
let str = "racecar";
let reversed = str.split("").reverse().join("");
if (str === reversed) {
    console.log(str + " is a Palindrome");
} else {
    console.log(str + " is not a Palindrome");
}
// Output: racecar is a Palindrome
```

## Architecture

### Components

1. **Lexer** (`lexer.py`): Tokenizes JavaScript source code
   - Handles strings, numbers, identifiers, keywords, and operators
   - Supports single-line and multi-line comments
   - Handles escape sequences in strings

2. **Parser** (`parser.py`): Converts tokens to an Abstract Syntax Tree (AST)
   - Recursive descent parser with operator precedence
   - Supports all JavaScript operators and statement types
   - Handles method chaining and complex expressions

3. **Interpreter** (`interpreter.py`): Executes the AST
   - Tree-walking interpreter
   - Manages variable scopes and function closures
   - Implements JavaScript semantics (truthiness, type coercion, etc.)

4. **AST Nodes** (`nodes.py`): Defines node classes for the syntax tree
   - Expression nodes, statement nodes, and operator nodes

5. **Main** (`main.py`): Entry point for the runtime

## Implementation Details

### Scoping
- Block scoping for `let` and `const` with proper closure support
- Variable lookup through scope chain (current scope → global scope)
- Lexical scoping for function closures

### Type System
- JavaScript type coercion for operators
- Loose equality (`==`) vs. strict equality (`===`)
- Proper `undefined` and `null` handling

### Function Calls
- Support for recursion
- Callback functions work with array methods
- Proper `this` handling in method calls

## Limitations and Future Enhancements

- **Arrow functions**: Currently not fully implemented
- **Spread operator in function calls**: Limited support
- **Regular expressions**: Not implemented
- **Async/await**: Not implemented
- **Classes**: Not implemented
- **Destructuring**: Not implemented
- **Template literals**: Not implemented

## License

This project is created for the Thunder Hackathon 2.0.
