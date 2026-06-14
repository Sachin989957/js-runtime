from nodes import *

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return ("EOF", None)

    def peek(self, offset=1):
        if self.pos + offset < len(self.tokens):
            return self.tokens[self.pos + offset]
        return ("EOF", None)

    def eat(self, token_type):
        if self.current()[0] == token_type:
            token = self.current()
            self.pos += 1
            return token
        raise Exception(f"Expected {token_type}, got {self.current()[0]}")

    def match(self, *token_types):
        return self.current()[0] in token_types

    def parse(self):
        program = []
        while self.current()[0] != "EOF":
            stmt = self.parse_statement()
            if stmt:
                program.append(stmt)
        return program

    def parse_statement(self):
        token_type = self.current()[0]

        if self.match("LET", "CONST"):
            return self.parse_variable_declaration()

        if token_type == "IF":
            return self.parse_if_statement()

        if token_type == "WHILE":
            return self.parse_while_statement()

        if token_type == "DO":
            return self.parse_do_while_statement()

        if token_type == "FOR":
            return self.parse_for_statement()

        if token_type == "FUNCTION":
            return self.parse_function_declaration()

        if token_type == "LBRACE":
            return self.parse_block_statement()

        if token_type == "RETURN":
            return self.parse_return_statement()

        if token_type == "BREAK":
            self.eat("BREAK")
            self.eat("SEMICOLON") if self.match("SEMICOLON") else None
            return BreakNode()

        if token_type == "CONTINUE":
            self.eat("CONTINUE")
            self.eat("SEMICOLON") if self.match("SEMICOLON") else None
            return ContinueNode()

        expr = self.parse_expression()
        if self.match("SEMICOLON"):
            self.eat("SEMICOLON")
        return expr

    def parse_variable_declaration(self):
        is_const = self.current()[0] == "CONST"
        self.eat("CONST" if is_const else "LET")
        
        name = self.eat("IDENTIFIER")[1]
        
        if self.match("ASSIGN"):
            self.eat("ASSIGN")
            value = self.parse_expression()
        else:
            value = UndefinedNode()

        if self.match("SEMICOLON"):
            self.eat("SEMICOLON")

        if is_const:
            return ConstNode(name, value)
        return LetNode(name, value)

    def parse_if_statement(self):
        self.eat("IF")
        self.eat("LPAREN")
        condition = self.parse_expression()
        self.eat("RPAREN")
        then_block = self.parse_statement()
        
        else_block = None
        if self.match("ELSE"):
            self.eat("ELSE")
            else_block = self.parse_statement()

        return IfNode(condition, then_block, else_block)

    def parse_while_statement(self):
        self.eat("WHILE")
        self.eat("LPAREN")
        condition = self.parse_expression()
        self.eat("RPAREN")
        body = self.parse_statement()
        return WhileNode(condition, body)

    def parse_do_while_statement(self):
        self.eat("DO")
        body = self.parse_statement()
        self.eat("WHILE")
        self.eat("LPAREN")
        condition = self.parse_expression()
        self.eat("RPAREN")
        if self.match("SEMICOLON"):
            self.eat("SEMICOLON")
        return DoWhileNode(body, condition)

    def parse_for_statement(self):
        self.eat("FOR")
        self.eat("LPAREN")
        
        # Init
        init = None
        if self.match("LET", "CONST"):
            init = self.parse_variable_declaration()
        elif not self.match("SEMICOLON"):
            init = self.parse_expression()
        
        if self.match("SEMICOLON"):
            self.eat("SEMICOLON")

        # Condition
        condition = None
        if not self.match("SEMICOLON"):
            condition = self.parse_expression()
        self.eat("SEMICOLON")

        # Update
        update = None
        if not self.match("RPAREN"):
            update = self.parse_expression()
        self.eat("RPAREN")

        body = self.parse_statement()
        return ForNode(init, condition, update, body)

    def parse_function_declaration(self):
        self.eat("FUNCTION")
        name = self.eat("IDENTIFIER")[1]
        
        self.eat("LPAREN")
        params = self.parse_parameters()
        self.eat("RPAREN")
        
        body = self.parse_block_statement()
        return FunctionNode(name, params, body)

    def parse_parameters(self):
        params = []
        if not self.match("RPAREN"):
            params.append(self.eat("IDENTIFIER")[1])
            while self.match("COMMA"):
                self.eat("COMMA")
                params.append(self.eat("IDENTIFIER")[1])
        return params

    def parse_block_statement(self):
        self.eat("LBRACE")
        statements = []
        while not self.match("RBRACE") and self.current()[0] != "EOF":
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        self.eat("RBRACE")
        return BlockNode(statements)

    def parse_return_statement(self):
        self.eat("RETURN")
        value = None
        if not self.match("SEMICOLON", "RBRACE", "EOF"):
            value = self.parse_expression()
        if self.match("SEMICOLON"):
            self.eat("SEMICOLON")
        return ReturnNode(value)

    def parse_expression(self):
        return self.parse_ternary()

    def parse_ternary(self):
        expr = self.parse_logical_or()
        if self.match("QUESTION"):
            self.eat("QUESTION")
            then_expr = self.parse_expression()
            self.eat("COLON")
            else_expr = self.parse_expression()
            return TernaryOpNode(expr, then_expr, else_expr)
        return expr

    def parse_logical_or(self):
        left = self.parse_logical_and()
        while self.match("OR"):
            op = self.eat("OR")[1]
            right = self.parse_logical_and()
            left = BinaryOpNode(left, op, right)
        return left

    def parse_logical_and(self):
        left = self.parse_bitwise_or()
        while self.match("AND"):
            op = self.eat("AND")[1]
            right = self.parse_bitwise_or()
            left = BinaryOpNode(left, op, right)
        return left

    def parse_bitwise_or(self):
        left = self.parse_bitwise_xor()
        while self.match("BITWISE_OR"):
            op = self.eat("BITWISE_OR")[1]
            right = self.parse_bitwise_xor()
            left = BinaryOpNode(left, op, right)
        return left

    def parse_bitwise_xor(self):
        left = self.parse_bitwise_and()
        while self.match("BITWISE_XOR"):
            op = self.eat("BITWISE_XOR")[1]
            right = self.parse_bitwise_and()
            left = BinaryOpNode(left, op, right)
        return left

    def parse_bitwise_and(self):
        left = self.parse_equality()
        while self.match("BITWISE_AND"):
            op = self.eat("BITWISE_AND")[1]
            right = self.parse_equality()
            left = BinaryOpNode(left, op, right)
        return left

    def parse_equality(self):
        left = self.parse_comparison()
        while self.match("EQUAL_EQUAL", "NOT_EQUAL", "STRICT_EQUAL", "STRICT_NOT_EQUAL"):
            op = self.current()[1]
            self.eat(self.current()[0])
            right = self.parse_comparison()
            left = BinaryOpNode(left, op, right)
        return left

    def parse_comparison(self):
        left = self.parse_additive()
        while self.match("LESS", "GREATER", "LESS_EQUAL", "GREATER_EQUAL"):
            op = self.current()[1]
            self.eat(self.current()[0])
            right = self.parse_additive()
            left = BinaryOpNode(left, op, right)
        return left

    def parse_additive(self):
        left = self.parse_multiplicative()
        while self.match("PLUS", "MINUS"):
            op = self.current()[1]
            self.eat(self.current()[0])
            right = self.parse_multiplicative()
            left = BinaryOpNode(left, op, right)
        return left

    def parse_multiplicative(self):
        left = self.parse_exponentiation()
        while self.match("MULTIPLY", "DIVIDE", "MODULO"):
            op = self.current()[1]
            self.eat(self.current()[0])
            right = self.parse_exponentiation()
            left = BinaryOpNode(left, op, right)
        return left

    def parse_exponentiation(self):
        left = self.parse_unary()
        if self.match("POW"):
            op = self.eat("POW")[1]
            right = self.parse_exponentiation()
            left = BinaryOpNode(left, op, right)
        return left

    def parse_unary(self):
        if self.match("NOT", "BITWISE_NOT", "PLUS", "MINUS", "TYPEOF"):
            op = self.current()[1]
            self.eat(self.current()[0])
            expr = self.parse_unary()
            return UnaryOpNode(op, expr)

        if self.match("INCREMENT", "DECREMENT"):
            op = self.current()[1]
            self.eat(self.current()[0])
            expr = self.parse_postfix()
            return UnaryOpNode(op, expr)

        return self.parse_postfix()

    def parse_postfix(self):
        expr = self.parse_call()

        while self.match("INCREMENT", "DECREMENT"):
            op = self.current()[1]
            self.eat(self.current()[0])
            expr = BinaryOpNode(expr, op + "_post", None)

        return expr

    def parse_call(self):
        expr = self.parse_primary()

        while True:
            if self.match("DOT"):
                self.eat("DOT")
                prop = self.eat("IDENTIFIER")[1]
                expr = MemberAccessNode(expr, prop)
            elif self.match("LBRACKET"):
                self.eat("LBRACKET")
                index = self.parse_expression()
                self.eat("RBRACKET")
                expr = ArrayAccessNode(expr, index)
            elif self.match("LPAREN"):
                self.eat("LPAREN")
                args = self.parse_arguments()
                self.eat("RPAREN")
                expr = FunctionCallNode(expr, args)
            else:
                break

        return expr

    def parse_member(self):
        return self.parse_call()

    def parse_arguments(self):
        args = []
        if not self.match("RPAREN"):
            if self.match("SPREAD"):
                self.eat("SPREAD")
                args.append(SpreadNode(self.parse_expression()))
            else:
                args.append(self.parse_expression())
            
            while self.match("COMMA"):
                self.eat("COMMA")
                if self.match("SPREAD"):
                    self.eat("SPREAD")
                    args.append(SpreadNode(self.parse_expression()))
                else:
                    args.append(self.parse_expression())
        return args

    def parse_primary(self):
        token_type = self.current()[0]

        if token_type == "IDENTIFIER":
            name = self.eat("IDENTIFIER")[1]
            
            if self.match("ASSIGN", "PLUS_EQUAL", "MINUS_EQUAL", "MULTIPLY_EQUAL", "DIVIDE_EQUAL", "MODULO_EQUAL"):
                op = self.current()[1]
                self.eat(self.current()[0])
                value = self.parse_expression()
                
                if op != '=':
                    base_op = op[:-1]
                    value = BinaryOpNode(VariableNode(name), base_op, value)
                
                return AssignmentNode(VariableNode(name), value)
            
            return VariableNode(name)

        if token_type == "NUMBER":
            num = self.eat("NUMBER")[1]
            return NumberNode(num)

        if token_type == "STRING":
            string = self.eat("STRING")[1]
            return StringNode(string)

        if token_type == "TRUE":
            self.eat("TRUE")
            return BooleanNode(True)

        if token_type == "FALSE":
            self.eat("FALSE")
            return BooleanNode(False)

        if token_type == "NULL":
            self.eat("NULL")
            return NullNode()

        if token_type == "UNDEFINED":
            self.eat("UNDEFINED")
            return UndefinedNode()

        if token_type == "LPAREN":
            self.eat("LPAREN")
            expr = self.parse_expression()
            self.eat("RPAREN")
            return expr

        if token_type == "LBRACKET":
            return self.parse_array()

        if token_type == "LBRACE":
            return self.parse_object()

        if token_type == "FUNCTION":
            return self.parse_function_expression()

        raise Exception(f"Unexpected token: {self.current()}")

    def parse_array(self):
        self.eat("LBRACKET")
        elements = []
        while not self.match("RBRACKET"):
            if self.match("COMMA"):
                elements.append(UndefinedNode())
                self.eat("COMMA")
            elif self.match("SPREAD"):
                self.eat("SPREAD")
                elements.append(SpreadNode(self.parse_expression()))
                if self.match("COMMA"):
                    self.eat("COMMA")
            else:
                elements.append(self.parse_expression())
                if self.match("COMMA"):
                    self.eat("COMMA")
                elif not self.match("RBRACKET"):
                    break
        self.eat("RBRACKET")
        return ArrayNode(elements)

    def parse_object(self):
        self.eat("LBRACE")
        properties = {}
        while not self.match("RBRACE"):
            if self.match("IDENTIFIER"):
                key = self.eat("IDENTIFIER")[1]
                self.eat("COLON")
                value = self.parse_expression()
                properties[key] = value
            elif self.match("STRING"):
                key = self.eat("STRING")[1]
                self.eat("COLON")
                value = self.parse_expression()
                properties[key] = value
            
            if self.match("COMMA"):
                self.eat("COMMA")
            elif not self.match("RBRACE"):
                break
        self.eat("RBRACE")
        return ObjectNode(properties)

    def parse_function_expression(self):
        self.eat("FUNCTION")
        name = None
        if self.match("IDENTIFIER"):
            name = self.eat("IDENTIFIER")[1]
        
        self.eat("LPAREN")
        params = self.parse_parameters()
        self.eat("RPAREN")
        
        body = self.parse_block_statement()
        return FunctionNode(name, params, body)


class TernaryOpNode:
    def __init__(self, condition, then_expr, else_expr):
        self.condition = condition
        self.then_expr = then_expr
        self.else_expr = else_expr
