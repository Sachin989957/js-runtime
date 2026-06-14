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
        raise Exception(f"Expected {token_type}, got {self.current()[0]} ('{self.current()[1]}')")

    def match(self, *token_types):
        return self.current()[0] in token_types

    def parse(self):
        program = []
        while self.current()[0] != "EOF":
            stmt = self.parse_statement()
            if stmt is not None:
                program.append(stmt)
        return program

    def parse_statement(self):
        token_type = self.current()[0]

        if self.match("LET", "CONST", "VAR"):
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

        if token_type == "SWITCH":
            return self.parse_switch_statement()

        if token_type == "LBRACE":
            return self.parse_block_statement()

        if token_type == "RETURN":
            return self.parse_return_statement()

        if token_type == "THROW":
            return self.parse_throw_statement()

        if token_type == "TRY":
            return self.parse_try_statement()

        if token_type == "BREAK":
            self.eat("BREAK")
            self.skip_semicolon()
            return BreakNode()

        if token_type == "CONTINUE":
            self.eat("CONTINUE")
            self.skip_semicolon()
            return ContinueNode()

        if token_type == "SEMICOLON":
            self.eat("SEMICOLON")
            return None

        expr = self.parse_expression()
        self.skip_semicolon()
        return expr

    def skip_semicolon(self):
        if self.match("SEMICOLON"):
            self.eat("SEMICOLON")

    def parse_variable_declaration(self):
        decl_type = self.current()[0]
        self.eat(decl_type)
        
        name = self.eat("IDENTIFIER")[1]
        
        if self.match("ASSIGN"):
            self.eat("ASSIGN")
            value = self.parse_expression()
        else:
            value = UndefinedNode()

        self.skip_semicolon()

        if decl_type == "CONST":
            return ConstNode(name, value)
        elif decl_type == "VAR":
            return VarNode(name, value)
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
        self.skip_semicolon()
        return DoWhileNode(body, condition)

    def parse_for_statement(self):
        self.eat("FOR")
        self.eat("LPAREN")
        
        # Check for for-of and for-in
        if self.match("LET", "CONST", "VAR"):
            saved_pos = self.pos
            decl_type = self.current()[0]
            self.eat(decl_type)
            var_name = self.eat("IDENTIFIER")[1]
            if self.match("OF"):
                self.eat("OF")
                iterable = self.parse_expression()
                self.eat("RPAREN")
                body = self.parse_statement()
                return ForOfNode(decl_type, var_name, iterable, body)
            elif self.match("IN"):
                self.eat("IN")
                iterable = self.parse_expression()
                self.eat("RPAREN")
                body = self.parse_statement()
                return ForInNode(decl_type, var_name, iterable, body)
            else:
                # Regular for with declaration; need to handle init
                if self.match("ASSIGN"):
                    self.eat("ASSIGN")
                    val = self.parse_expression()
                else:
                    val = UndefinedNode()
                if decl_type == "CONST":
                    init = ConstNode(var_name, val)
                elif decl_type == "VAR":
                    init = VarNode(var_name, val)
                else:
                    init = LetNode(var_name, val)
                self.skip_semicolon()
        elif not self.match("SEMICOLON"):
            init = self.parse_expression()
            self.skip_semicolon()
        else:
            init = None
            self.skip_semicolon()

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

    def parse_switch_statement(self):
        self.eat("SWITCH")
        self.eat("LPAREN")
        expression = self.parse_expression()
        self.eat("RPAREN")
        self.eat("LBRACE")
        
        cases = []
        default = None
        
        while not self.match("RBRACE") and not self.match("EOF"):
            if self.match("CASE"):
                self.eat("CASE")
                case_val = self.parse_expression()
                self.eat("COLON")
                stmts = []
                while not self.match("CASE") and not self.match("DEFAULT") and not self.match("RBRACE") and not self.match("EOF"):
                    s = self.parse_statement()
                    if s is not None:
                        stmts.append(s)
                cases.append((case_val, stmts))
            elif self.match("DEFAULT"):
                self.eat("DEFAULT")
                self.eat("COLON")
                stmts = []
                while not self.match("CASE") and not self.match("RBRACE") and not self.match("EOF"):
                    s = self.parse_statement()
                    if s is not None:
                        stmts.append(s)
                default = stmts
            else:
                break
        
        self.eat("RBRACE")
        return SwitchNode(expression, cases, default)

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
            if self.match("SPREAD"):
                self.eat("SPREAD")
                params.append("..." + self.eat("IDENTIFIER")[1])
            else:
                p = self.eat("IDENTIFIER")[1]
                if self.match("ASSIGN"):
                    self.eat("ASSIGN")
                    self.parse_expression()  # default param - simplified, just parse and ignore
                params.append(p)
            while self.match("COMMA"):
                self.eat("COMMA")
                if self.match("SPREAD"):
                    self.eat("SPREAD")
                    params.append("..." + self.eat("IDENTIFIER")[1])
                else:
                    p = self.eat("IDENTIFIER")[1]
                    if self.match("ASSIGN"):
                        self.eat("ASSIGN")
                        self.parse_expression()
                    params.append(p)
        return params

    def parse_block_statement(self):
        self.eat("LBRACE")
        statements = []
        while not self.match("RBRACE") and self.current()[0] != "EOF":
            stmt = self.parse_statement()
            if stmt is not None:
                statements.append(stmt)
        self.eat("RBRACE")
        return BlockNode(statements)

    def parse_return_statement(self):
        self.eat("RETURN")
        value = None
        if not self.match("SEMICOLON", "RBRACE", "EOF"):
            value = self.parse_expression()
        self.skip_semicolon()
        return ReturnNode(value)

    def parse_throw_statement(self):
        self.eat("THROW")
        value = self.parse_expression()
        self.skip_semicolon()
        return ThrowNode(value)

    def parse_try_statement(self):
        self.eat("TRY")
        try_block = self.parse_block_statement()
        catch_var = None
        catch_block = None
        finally_block = None
        if self.match("CATCH"):
            self.eat("CATCH")
            if self.match("LPAREN"):
                self.eat("LPAREN")
                catch_var = self.eat("IDENTIFIER")[1]
                self.eat("RPAREN")
            catch_block = self.parse_block_statement()
        if self.match("FINALLY"):
            self.eat("FINALLY")
            finally_block = self.parse_block_statement()
        return TryCatchNode(try_block, catch_var, catch_block, finally_block)

    def parse_expression(self):
        return self.parse_assignment()

    def parse_assignment(self):
        expr = self.parse_ternary()
        if self.match("ASSIGN", "PLUS_EQUAL", "MINUS_EQUAL", "MULTIPLY_EQUAL", "DIVIDE_EQUAL", "MODULO_EQUAL", "POW_EQUAL"):
            op = self.current()[1]
            self.eat(self.current()[0])
            value = self.parse_assignment()
            if op != '=':
                base_op = op[:-1]
                value = BinaryOpNode(expr, base_op, value)
            return AssignmentNode(expr, value)
        return expr

    def parse_ternary(self):
        expr = self.parse_logical_or()
        if self.match("QUESTION"):
            self.eat("QUESTION")
            then_expr = self.parse_assignment()
            self.eat("COLON")
            else_expr = self.parse_assignment()
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
        while self.match("LESS", "GREATER", "LESS_EQUAL", "GREATER_EQUAL", "INSTANCEOF", "IN"):
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
        if self.match("NOT"):
            self.eat("NOT")
            expr = self.parse_unary()
            return UnaryOpNode("!", expr)
        if self.match("BITWISE_NOT"):
            self.eat("BITWISE_NOT")
            expr = self.parse_unary()
            return UnaryOpNode("~", expr)
        if self.match("MINUS"):
            self.eat("MINUS")
            expr = self.parse_unary()
            return UnaryOpNode("-", expr)
        if self.match("PLUS"):
            self.eat("PLUS")
            expr = self.parse_unary()
            return UnaryOpNode("+", expr)
        if self.match("TYPEOF"):
            self.eat("TYPEOF")
            expr = self.parse_unary()
            return UnaryOpNode("typeof", expr)
        if self.match("INCREMENT"):
            self.eat("INCREMENT")
            expr = self.parse_postfix()
            return UnaryOpNode("++", expr)
        if self.match("DECREMENT"):
            self.eat("DECREMENT")
            expr = self.parse_postfix()
            return UnaryOpNode("--", expr)
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
            elif self.match("OPTIONAL_CHAIN"):
                self.eat("OPTIONAL_CHAIN")
                prop = self.eat("IDENTIFIER")[1]
                expr = MemberAccessNode(expr, prop)  # simplified - treat like regular
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

    def parse_arguments(self):
        args = []
        if not self.match("RPAREN"):
            if self.match("SPREAD"):
                self.eat("SPREAD")
                args.append(SpreadNode(self.parse_assignment()))
            else:
                args.append(self.parse_assignment())
            
            while self.match("COMMA"):
                self.eat("COMMA")
                if self.match("RPAREN"):
                    break
                if self.match("SPREAD"):
                    self.eat("SPREAD")
                    args.append(SpreadNode(self.parse_assignment()))
                else:
                    args.append(self.parse_assignment())
        return args

    def parse_primary(self):
        token_type = self.current()[0]

        if token_type == "NUMBER":
            return NumberNode(self.eat("NUMBER")[1])

        if token_type == "STRING":
            return StringNode(self.eat("STRING")[1])

        if token_type == "TEMPLATE_STRING":
            return self.parse_template_literal()

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

        if token_type == "THIS":
            self.eat("THIS")
            return VariableNode("this")

        if token_type == "NEW":
            return self.parse_new()

        if token_type == "IDENTIFIER":
            name = self.eat("IDENTIFIER")[1]
            # Check for arrow function: identifier => ...
            if self.match("ARROW"):
                self.eat("ARROW")
                body = self.parse_arrow_body()
                return ArrowFunctionNode([name], body)
            return VariableNode(name)

        if token_type == "LPAREN":
            # Could be arrow function: (params) => body
            saved_pos = self.pos
            try:
                arrow_node = self.try_parse_arrow_function()
                if arrow_node:
                    return arrow_node
            except:
                self.pos = saved_pos
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

    def try_parse_arrow_function(self):
        """Try to parse (params) => body. Returns None if not an arrow function."""
        self.eat("LPAREN")
        params = []
        # Parse params list
        if not self.match("RPAREN"):
            if self.match("SPREAD"):
                self.eat("SPREAD")
                params.append("..." + self.eat("IDENTIFIER")[1])
            elif self.match("IDENTIFIER"):
                p = self.eat("IDENTIFIER")[1]
                if self.match("ASSIGN"):
                    self.eat("ASSIGN")
                    self.parse_expression()  # default, simplified
                params.append(p)
                while self.match("COMMA"):
                    self.eat("COMMA")
                    if self.match("RPAREN"):
                        break
                    if self.match("SPREAD"):
                        self.eat("SPREAD")
                        params.append("..." + self.eat("IDENTIFIER")[1])
                    elif self.match("IDENTIFIER"):
                        p = self.eat("IDENTIFIER")[1]
                        if self.match("ASSIGN"):
                            self.eat("ASSIGN")
                            self.parse_expression()
                        params.append(p)
                    else:
                        raise Exception("Expected identifier in arrow params")
            else:
                raise Exception("Not an arrow function")
        if not self.match("RPAREN"):
            raise Exception("Expected ) in arrow params")
        self.eat("RPAREN")
        if not self.match("ARROW"):
            raise Exception("Not an arrow function")
        self.eat("ARROW")
        body = self.parse_arrow_body()
        return ArrowFunctionNode(params, body)

    def parse_arrow_body(self):
        if self.match("LBRACE"):
            return self.parse_block_statement()
        else:
            # Expression body - wrap in implicit return
            expr = self.parse_assignment()
            return BlockNode([ReturnNode(expr)])

    def parse_new(self):
        self.eat("NEW")
        constructor = self.eat("IDENTIFIER")[1]
        args = []
        if self.match("LPAREN"):
            self.eat("LPAREN")
            args = self.parse_arguments()
            self.eat("RPAREN")
        return NewNode(VariableNode(constructor), args)

    def parse_template_literal(self):
        # Template literal token contains the raw string
        raw = self.eat("TEMPLATE_STRING")[1]
        # Parse ${...} expressions from the raw string
        parts = []
        i = 0
        current_str = ""
        while i < len(raw):
            if raw[i] == '$' and i + 1 < len(raw) and raw[i+1] == '{':
                if current_str:
                    parts.append((False, current_str))
                    current_str = ""
                i += 2
                depth = 1
                expr_str = ""
                while i < len(raw) and depth > 0:
                    if raw[i] == '{':
                        depth += 1
                    elif raw[i] == '}':
                        depth -= 1
                        if depth == 0:
                            break
                    expr_str += raw[i]
                    i += 1
                i += 1  # skip closing }
                # Parse the expression
                from lexer import Lexer
                sub_tokens = Lexer(expr_str).tokenize()
                sub_parser = Parser(sub_tokens)
                expr_node = sub_parser.parse_expression()
                parts.append((True, expr_node))
            else:
                current_str += raw[i]
                i += 1
        if current_str:
            parts.append((False, current_str))
        return TemplateLiteralNode(parts)

    def parse_array(self):
        self.eat("LBRACKET")
        elements = []
        while not self.match("RBRACKET") and not self.match("EOF"):
            if self.match("COMMA"):
                elements.append(UndefinedNode())
                self.eat("COMMA")
            elif self.match("SPREAD"):
                self.eat("SPREAD")
                elements.append(SpreadNode(self.parse_assignment()))
                if self.match("COMMA"):
                    self.eat("COMMA")
            else:
                elements.append(self.parse_assignment())
                if self.match("COMMA"):
                    self.eat("COMMA")
                elif not self.match("RBRACKET"):
                    break
        self.eat("RBRACKET")
        return ArrayNode(elements)

    def parse_object(self):
        self.eat("LBRACE")
        properties = {}
        while not self.match("RBRACE") and not self.match("EOF"):
            if self.match("SPREAD"):
                self.eat("SPREAD")
                # Spread in object - simplified, skip for now
                self.parse_expression()
            elif self.match("IDENTIFIER"):
                key = self.eat("IDENTIFIER")[1]
                if self.match("COLON"):
                    self.eat("COLON")
                    value = self.parse_assignment()
                    properties[key] = value
                elif self.match("LPAREN"):
                    # Method shorthand: method() { }
                    self.eat("LPAREN")
                    params = self.parse_parameters()
                    self.eat("RPAREN")
                    body = self.parse_block_statement()
                    properties[key] = FunctionNode(key, params, body)
                else:
                    # Shorthand property: { x } => { x: x }
                    properties[key] = VariableNode(key)
            elif self.match("STRING"):
                key = self.eat("STRING")[1]
                self.eat("COLON")
                value = self.parse_assignment()
                properties[key] = value
            elif self.match("NUMBER"):
                key = str(self.eat("NUMBER")[1])
                self.eat("COLON")
                value = self.parse_assignment()
                properties[key] = value
            else:
                break

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