import re

class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.keywords = {
            'let', 'const', 'var', 'if', 'else', 'for', 'while', 'do', 'break',
            'continue', 'return', 'function', 'true', 'false', 'null', 'undefined',
            'switch', 'case', 'default', 'new', 'typeof', 'instanceof', 'in',
            'of', 'class', 'extends', 'static', 'async', 'await', 'try', 'catch',
            'finally', 'throw', 'this', 'super'
        }

    def tokenize(self):
        tokens = []

        while self.pos < len(self.text):
            ch = self.text[self.pos]

            # Skip whitespace and newlines
            if ch.isspace():
                self.pos += 1
                continue

            # Skip comments
            if ch == '/' and self.pos + 1 < len(self.text):
                if self.text[self.pos + 1] == '/':
                    while self.pos < len(self.text) and self.text[self.pos] != '\n':
                        self.pos += 1
                    continue
                elif self.text[self.pos + 1] == '*':
                    self.pos += 2
                    while self.pos + 1 < len(self.text):
                        if self.text[self.pos] == '*' and self.text[self.pos + 1] == '/':
                            self.pos += 2
                            break
                        self.pos += 1
                    continue

            # String literals
            if ch in ['"', "'"]:
                quote = ch
                self.pos += 1
                string_val = ""
                while self.pos < len(self.text) and self.text[self.pos] != quote:
                    if self.text[self.pos] == '\\' and self.pos + 1 < len(self.text):
                        next_ch = self.text[self.pos + 1]
                        if next_ch == 'n':
                            string_val += '\n'
                        elif next_ch == 't':
                            string_val += '\t'
                        elif next_ch == 'r':
                            string_val += '\r'
                        elif next_ch == '\\':
                            string_val += '\\'
                        elif next_ch == quote:
                            string_val += quote
                        else:
                            string_val += next_ch
                        self.pos += 2
                    else:
                        string_val += self.text[self.pos]
                        self.pos += 1
                if self.pos < len(self.text):
                    self.pos += 1
                tokens.append(("STRING", string_val))
                continue

            # Template literals (backtick)
            if ch == '`':
                self.pos += 1
                string_val = ""
                while self.pos < len(self.text) and self.text[self.pos] != '`':
                    if self.text[self.pos] == '\\' and self.pos + 1 < len(self.text):
                        next_ch = self.text[self.pos + 1]
                        if next_ch == 'n':
                            string_val += '\n'
                        elif next_ch == 't':
                            string_val += '\t'
                        elif next_ch == '`':
                            string_val += '`'
                        elif next_ch == '\\':
                            string_val += '\\'
                        else:
                            string_val += next_ch
                        self.pos += 2
                    else:
                        string_val += self.text[self.pos]
                        self.pos += 1
                if self.pos < len(self.text):
                    self.pos += 1
                tokens.append(("TEMPLATE_STRING", string_val))
                continue

            # Numbers
            if ch.isdigit():
                num = ""
                while self.pos < len(self.text) and (self.text[self.pos].isdigit() or self.text[self.pos] == '.'):
                    num += self.text[self.pos]
                    self.pos += 1
                if '.' in num:
                    tokens.append(("NUMBER", float(num)))
                else:
                    tokens.append(("NUMBER", int(num)))
                continue

            # Identifiers and keywords
            if ch.isalpha() or ch == '_' or ch == '$':
                word = ""
                while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] in ['_', '$']):
                    word += self.text[self.pos]
                    self.pos += 1

                if word in self.keywords:
                    tokens.append((word.upper(), word))
                else:
                    tokens.append(("IDENTIFIER", word))
                continue

            # Multi-character operators
            if self.pos + 2 < len(self.text):
                three_char = self.text[self.pos:self.pos+3]
                if three_char == '===':
                    tokens.append(("STRICT_EQUAL", "==="))
                    self.pos += 3
                    continue
                elif three_char == '!==':
                    tokens.append(("STRICT_NOT_EQUAL", "!=="))
                    self.pos += 3
                    continue
                elif three_char == '...':
                    tokens.append(("SPREAD", "..."))
                    self.pos += 3
                    continue
                elif three_char == '**=':
                    tokens.append(("POW_EQUAL", "**="))
                    self.pos += 3
                    continue

            if self.pos + 1 < len(self.text):
                two_char = self.text[self.pos:self.pos+2]
                if two_char == '==':
                    tokens.append(("EQUAL_EQUAL", "=="))
                    self.pos += 2
                    continue
                elif two_char == '!=':
                    tokens.append(("NOT_EQUAL", "!="))
                    self.pos += 2
                    continue
                elif two_char == '<=':
                    tokens.append(("LESS_EQUAL", "<="))
                    self.pos += 2
                    continue
                elif two_char == '>=':
                    tokens.append(("GREATER_EQUAL", ">="))
                    self.pos += 2
                    continue
                elif two_char == '&&':
                    tokens.append(("AND", "&&"))
                    self.pos += 2
                    continue
                elif two_char == '||':
                    tokens.append(("OR", "||"))
                    self.pos += 2
                    continue
                elif two_char == '++':
                    tokens.append(("INCREMENT", "++"))
                    self.pos += 2
                    continue
                elif two_char == '--':
                    tokens.append(("DECREMENT", "--"))
                    self.pos += 2
                    continue
                elif two_char == '+=':
                    tokens.append(("PLUS_EQUAL", "+="))
                    self.pos += 2
                    continue
                elif two_char == '-=':
                    tokens.append(("MINUS_EQUAL", "-="))
                    self.pos += 2
                    continue
                elif two_char == '*=':
                    tokens.append(("MULTIPLY_EQUAL", "*="))
                    self.pos += 2
                    continue
                elif two_char == '/=':
                    tokens.append(("DIVIDE_EQUAL", "/="))
                    self.pos += 2
                    continue
                elif two_char == '%=':
                    tokens.append(("MODULO_EQUAL", "%="))
                    self.pos += 2
                    continue
                elif two_char == '=>':
                    tokens.append(("ARROW", "=>"))
                    self.pos += 2
                    continue
                elif two_char == '**':
                    tokens.append(("POW", "**"))
                    self.pos += 2
                    continue
                elif two_char == '?.':
                    tokens.append(("OPTIONAL_CHAIN", "?."))
                    self.pos += 2
                    continue

            # Single character tokens
            char_tokens = {
                '+': 'PLUS',
                '-': 'MINUS',
                '*': 'MULTIPLY',
                '/': 'DIVIDE',
                '%': 'MODULO',
                '=': 'ASSIGN',
                '<': 'LESS',
                '>': 'GREATER',
                '!': 'NOT',
                '&': 'BITWISE_AND',
                '|': 'BITWISE_OR',
                '^': 'BITWISE_XOR',
                '~': 'BITWISE_NOT',
                '?': 'QUESTION',
                ':': 'COLON',
                ';': 'SEMICOLON',
                ',': 'COMMA',
                '.': 'DOT',
                '(': 'LPAREN',
                ')': 'RPAREN',
                '[': 'LBRACKET',
                ']': 'RBRACKET',
                '{': 'LBRACE',
                '}': 'RBRACE',
            }

            if ch in char_tokens:
                tokens.append((char_tokens[ch], ch))
                self.pos += 1
                continue

            self.pos += 1

        tokens.append(("EOF", None))
        return tokens