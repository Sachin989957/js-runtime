import math
import random
from datetime import datetime
from nodes import *

class BreakException(Exception):
    pass

class ContinueException(Exception):
    pass

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class JSFunction:
    def __init__(self, params, body, closure):
        self.params = params
        self.body = body
        self.closure = closure

class JSObject:
    def __init__(self, properties=None):
        self.properties = properties or {}

    def get(self, key):
        return self.properties.get(str(key))

    def set(self, key, value):
        self.properties[str(key)] = value

class JSArray:
    def __init__(self, elements=None):
        self.elements = elements or []

    def __repr__(self):
        return f"JSArray({self.elements})"

class Interpreter:
    def __init__(self):
        self.global_scope = self.create_global_scope()
        self.scopes = [self.global_scope]

    def create_global_scope(self):
        return {
            'console': {
                'log': lambda *args: print(*[self.js_to_string(arg) for arg in args], end='\n')
            },
            'Math': {
                'floor': math.floor,
                'ceil': math.ceil,
                'round': round,
                'abs': abs,
                'sqrt': math.sqrt,
                'pow': pow,
                'max': lambda *args: max(args) if args else float('-inf'),
                'min': lambda *args: min(args) if args else float('inf'),
                'random': random.random,
                'PI': math.pi,
                'E': math.e,
            },
            'parseInt': int,
            'parseFloat': float,
            'isNaN': lambda x: x != x,
            'undefined': None,
            'null': None,
            'Array': {
                'isArray': lambda x: isinstance(x, JSArray)
            },
            'String': {
                'fromCharCode': lambda *codes: ''.join(chr(int(c)) for c in codes)
            },
            'Date': self.create_date_constructor(),
            'Object': {
                'keys': lambda obj: JSArray([k for k in obj.properties.keys()]) if isinstance(obj, JSObject) else JSArray([]),
            }
        }

    def create_date_constructor(self):
        def date_constructor(*args):
            if not args:
                return datetime.now()
            return datetime(*args)
        return date_constructor

    def current_scope(self):
        return self.scopes[-1]

    def push_scope(self):
        self.scopes.append({})

    def pop_scope(self):
        self.scopes.pop()

    def get_variable(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise Exception(f"Undefined variable: {name}")

    def set_variable(self, name, value):
        for scope in reversed(self.scopes):
            if name in scope:
                scope[name] = value
                return
        self.current_scope()[name] = value

    def define_variable(self, name, value):
        self.current_scope()[name] = value

    def js_to_string(self, value):
        if value is None:
            return "undefined"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, JSArray):
            return ",".join(self.js_to_string(elem) for elem in value.elements)
        if isinstance(value, JSObject):
            return "[object Object]"
        if isinstance(value, JSFunction):
            return "[Function]"
        if isinstance(value, (int, float)):
            if isinstance(value, float) and value.is_integer():
                return str(int(value))
            return str(value)
        return str(value)

    def is_truthy(self, value):
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0 and not math.isnan(value)
        if isinstance(value, str):
            return value != ""
        return True

    def execute(self, node):
        if node is None:
            return None

        if isinstance(node, list):
            result = None
            for stmt in node:
                result = self.execute(stmt)
            return result

        if isinstance(node, NumberNode):
            return node.value

        if isinstance(node, StringNode):
            return node.value

        if isinstance(node, BooleanNode):
            return node.value

        if isinstance(node, NullNode):
            return None

        if isinstance(node, UndefinedNode):
            return None

        if isinstance(node, VariableNode):
            return self.get_variable(node.name)

        if isinstance(node, BinaryOpNode):
            return self.execute_binary_op(node)

        if isinstance(node, UnaryOpNode):
            return self.execute_unary_op(node)

        if isinstance(node, LetNode):
            value = self.execute(node.value)
            self.define_variable(node.name, value)
            return value

        if isinstance(node, ConstNode):
            value = self.execute(node.value)
            self.define_variable(node.name, value)
            return value

        if isinstance(node, AssignmentNode):
            if isinstance(node.target, VariableNode):
                value = self.execute(node.value)
                self.set_variable(node.target.name, value)
                return value
            elif isinstance(node.target, MemberAccessNode):
                obj = self.execute(node.target.object)
                value = self.execute(node.value)
                if isinstance(obj, JSObject):
                    obj.set(node.target.property, value)
                elif isinstance(obj, JSArray):
                    try:
                        idx = int(float(node.target.property))
                        if idx < len(obj.elements):
                            obj.elements[idx] = value
                    except:
                        pass
                return value
            elif isinstance(node.target, ArrayAccessNode):
                obj = self.execute(node.target.array)
                index = self.execute(node.target.index)
                value = self.execute(node.value)
                if isinstance(obj, JSArray):
                    idx = int(float(index))
                    if idx < len(obj.elements):
                        obj.elements[idx] = value
                return value
            return None

        if isinstance(node, IfNode):
            condition = self.execute(node.condition)
            if self.is_truthy(condition):
                return self.execute(node.then_block)
            elif node.else_block:
                return self.execute(node.else_block)
            return None

        if isinstance(node, WhileNode):
            result = None
            while self.is_truthy(self.execute(node.condition)):
                try:
                    result = self.execute(node.body)
                except BreakException:
                    break
                except ContinueException:
                    continue
            return result

        if isinstance(node, DoWhileNode):
            result = None
            while True:
                try:
                    result = self.execute(node.body)
                except BreakException:
                    break
                except ContinueException:
                    pass
                if not self.is_truthy(self.execute(node.condition)):
                    break
            return result

        if isinstance(node, ForNode):
            self.push_scope()
            result = None

            if node.init:
                self.execute(node.init)

            while node.condition is None or self.is_truthy(self.execute(node.condition)):
                try:
                    result = self.execute(node.body)
                except BreakException:
                    break
                except ContinueException:
                    pass

                if node.update:
                    self.execute(node.update)

            old_scope = self.scopes[-1]
            self.pop_scope()
            
            for key in list(old_scope.keys()):
                if key in self.current_scope() or key not in self.scopes[0]:
                    self.current_scope()[key] = old_scope[key]

            return result

        if isinstance(node, BlockNode):
            self.push_scope()
            result = None
            for stmt in node.statements:
                result = self.execute(stmt)
                if isinstance(stmt, ReturnNode) or isinstance(result, type(None)) and any(isinstance(s, ReturnNode) for s in [stmt]):
                    pass
            self.pop_scope()
            return result

        if isinstance(node, FunctionNode):
            params = node.params
            body = node.body
            closure = dict(self.current_scope())
            func = JSFunction(params, body, closure)
            if node.name:
                self.define_variable(node.name, func)
            return func

        if isinstance(node, FunctionCallNode):
            func = self.execute(node.func)
            args = [self.execute(arg) for arg in node.args]

            if isinstance(node.func, MemberAccessNode):
                obj = self.execute(node.func.object)
                method_name = node.func.property

                if isinstance(obj, JSArray):
                    method = self.get_array_method(obj, method_name)
                    if method:
                        return method(*args)

                if isinstance(obj, str):
                    method = self.get_string_method(obj, method_name)
                    if method:
                        return method(*args)

                if isinstance(obj, JSObject) and method_name in obj.properties:
                    func = obj.properties[method_name]
                    if isinstance(func, JSFunction):
                        return self.call_function(func, args)

            if isinstance(func, JSFunction):
                return self.call_function(func, args)

            if callable(func):
                return func(*args)

            raise Exception(f"Cannot call {type(func)}")

        if isinstance(node, ReturnNode):
            value = self.execute(node.value) if node.value else None
            raise ReturnException(value)

        if isinstance(node, BreakNode):
            raise BreakException()

        if isinstance(node, ContinueNode):
            raise ContinueException()

        if isinstance(node, ArrayNode):
            elements = []
            for elem in node.elements:
                if isinstance(elem, SpreadNode):
                    spread_arr = self.execute(elem.value)
                    if isinstance(spread_arr, JSArray):
                        elements.extend(spread_arr.elements)
                else:
                    elements.append(self.execute(elem))
            return JSArray(elements)

        if isinstance(node, ObjectNode):
            properties = {}
            for key, value in node.properties.items():
                properties[key] = self.execute(value)
            return JSObject(properties)

        if isinstance(node, ArrayAccessNode):
            array = self.execute(node.array)
            index = self.execute(node.index)
            if isinstance(array, JSArray):
                idx = int(float(index))
                if 0 <= idx < len(array.elements):
                    return array.elements[idx]
                return None
            return None

        if isinstance(node, MemberAccessNode):
            obj = self.execute(node.object)
            if isinstance(obj, JSObject):
                return obj.get(node.property)
            if isinstance(obj, dict):
                return obj.get(node.property)
            return None

        if isinstance(node, TernaryOpNode):
            condition = self.execute(node.condition)
            if self.is_truthy(condition):
                return self.execute(node.then_expr)
            else:
                return self.execute(node.else_expr)

        return None

    def execute_binary_op(self, node):
        left = self.execute(node.left)
        right = self.execute(node.right)

        if node.op == "+":
            if isinstance(left, str) or isinstance(right, str):
                return self.js_to_string(left) + self.js_to_string(right)
            return left + right

        if node.op == "-":
            return left - right

        if node.op == "*":
            return left * right

        if node.op == "/":
            if right == 0:
                return float('inf') if left >= 0 else float('-inf')
            return left / right

        if node.op == "%":
            return left % right

        if node.op == "**":
            return left ** right

        if node.op == "==":
            return self.loose_equal(left, right)

        if node.op == "!=":
            return not self.loose_equal(left, right)

        if node.op == "===":
            return self.strict_equal(left, right)

        if node.op == "!==":
            return not self.strict_equal(left, right)

        if node.op == "<":
            return left < right

        if node.op == ">":
            return left > right

        if node.op == "<=":
            return left <= right

        if node.op == ">=":
            return left >= right

        if node.op == "&&":
            if not self.is_truthy(left):
                return left
            return right

        if node.op == "||":
            if self.is_truthy(left):
                return left
            return right

        if node.op == "&":
            return int(left) & int(right)

        if node.op == "|":
            return int(left) | int(right)

        if node.op == "^":
            return int(left) ^ int(right)

        if node.op == "<<":
            return int(left) << int(right)

        if node.op == ">>":
            return int(left) >> int(right)

        if node.op == ">>>":
            return int(left) >> int(right)

        raise Exception(f"Unknown binary operator: {node.op}")

    def execute_unary_op(self, node):
        operand = self.execute(node.operand)

        if node.op == "!":
            return not self.is_truthy(operand)

        if node.op == "-":
            return -operand

        if node.op == "+":
            return +operand

        if node.op == "~":
            return ~int(operand)

        if node.op == "typeof":
            if operand is None:
                return "undefined"
            if isinstance(operand, bool):
                return "boolean"
            if isinstance(operand, (int, float)):
                return "number"
            if isinstance(operand, str):
                return "string"
            if isinstance(operand, JSFunction):
                return "function"
            if isinstance(operand, (JSObject, JSArray)):
                return "object"
            return "object"

        if node.op == "++":
            if isinstance(node.operand, VariableNode):
                val = self.get_variable(node.operand.name)
                new_val = val + 1
                self.set_variable(node.operand.name, new_val)
                return new_val
            return operand + 1

        if node.op == "--":
            if isinstance(node.operand, VariableNode):
                val = self.get_variable(node.operand.name)
                new_val = val - 1
                self.set_variable(node.operand.name, new_val)
                return new_val
            return operand - 1

        if node.op == "++_post":
            if isinstance(node.operand, VariableNode):
                val = self.get_variable(node.operand.name)
                self.set_variable(node.operand.name, val + 1)
                return val
            return operand

        if node.op == "--_post":
            if isinstance(node.operand, VariableNode):
                val = self.get_variable(node.operand.name)
                self.set_variable(node.operand.name, val - 1)
                return val
            return operand

        raise Exception(f"Unknown unary operator: {node.op}")

    def strict_equal(self, left, right):
        if type(left) != type(right):
            return False
        if left is None:
            return right is None
        return left == right

    def loose_equal(self, left, right):
        if type(left) == type(right):
            return left == right
        if left is None and right is None:
            return True
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return left == right
        if isinstance(left, str) and isinstance(right, (int, float)):
            try:
                return float(left) == right
            except:
                return False
        if isinstance(left, (int, float)) and isinstance(right, str):
            try:
                return left == float(right)
            except:
                return False
        return False

    def call_function(self, func, args):
        self.push_scope()
        for key, value in func.closure.items():
            self.current_scope()[key] = value

        for i, param in enumerate(func.params):
            if i < len(args):
                self.define_variable(param, args[i])
            else:
                self.define_variable(param, None)

        try:
            self.execute(func.body)
            result = None
        except ReturnException as e:
            result = e.value

        self.pop_scope()
        return result

    def get_array_method(self, array, method_name):
        if method_name == "push":
            return lambda *items: (array.elements.extend(items), len(array.elements) - 1)[1]

        if method_name == "pop":
            return lambda: array.elements.pop() if array.elements else None

        if method_name == "shift":
            return lambda: array.elements.pop(0) if array.elements else None

        if method_name == "unshift":
            return lambda *items: (array.elements[:0] = items, len(array.elements))[1]

        if method_name == "slice":
            def slice_method(start=0, end=None):
                start = int(start)
                if end is None:
                    return JSArray(array.elements[start:])
                return JSArray(array.elements[start:int(end)])
            return slice_method

        if method_name == "splice":
            def splice_method(start, delete_count=0, *items):
                start = int(start)
                delete_count = int(delete_count)
                removed = JSArray(array.elements[start:start + delete_count])
                array.elements[start:start + delete_count] = items
                return removed
            return splice_method

        if method_name == "concat":
            def concat_method(*items):
                result = list(array.elements)
                for item in items:
                    if isinstance(item, JSArray):
                        result.extend(item.elements)
                    else:
                        result.append(item)
                return JSArray(result)
            return concat_method

        if method_name == "join":
            def join_method(sep=","):
                return sep.join(self.js_to_string(elem) for elem in array.elements)
            return join_method

        if method_name == "reverse":
            return lambda: (array.elements.reverse(), array)[1]

        if method_name == "sort":
            return lambda: (array.elements.sort(), array)[1]

        if method_name == "includes":
            def includes_method(item):
                for elem in array.elements:
                    if self.strict_equal(elem, item):
                        return True
                return False
            return includes_method

        if method_name == "indexOf":
            def index_of_method(item):
                for i, elem in enumerate(array.elements):
                    if self.strict_equal(elem, item):
                        return i
                return -1
            return index_of_method

        if method_name == "map":
            def map_method(callback):
                result = []
                for i, elem in enumerate(array.elements):
                    if isinstance(callback, JSFunction):
                        val = self.call_function(callback, [elem, i, array])
                    else:
                        val = callback(elem, i, array)
                    result.append(val)
                return JSArray(result)
            return map_method

        if method_name == "filter":
            def filter_method(callback):
                result = []
                for i, elem in enumerate(array.elements):
                    if isinstance(callback, JSFunction):
                        should_include = self.call_function(callback, [elem, i, array])
                    else:
                        should_include = callback(elem, i, array)
                    if self.is_truthy(should_include):
                        result.append(elem)
                return JSArray(result)
            return filter_method

        if method_name == "reduce":
            def reduce_method(callback, initial=None):
                if len(array.elements) == 0 and initial is None:
                    raise Exception("Reduce of empty array with no initial value")
                
                start_idx = 0
                if initial is None:
                    accumulator = array.elements[0]
                    start_idx = 1
                else:
                    accumulator = initial

                for i in range(start_idx, len(array.elements)):
                    if isinstance(callback, JSFunction):
                        accumulator = self.call_function(callback, [accumulator, array.elements[i], i, array])
                    else:
                        accumulator = callback(accumulator, array.elements[i], i, array)
                return accumulator
            return reduce_method

        if method_name == "find":
            def find_method(callback):
                for i, elem in enumerate(array.elements):
                    if isinstance(callback, JSFunction):
                        found = self.call_function(callback, [elem, i, array])
                    else:
                        found = callback(elem, i, array)
                    if self.is_truthy(found):
                        return elem
                return None
            return find_method

        if method_name == "some":
            def some_method(callback):
                for i, elem in enumerate(array.elements):
                    if isinstance(callback, JSFunction):
                        result = self.call_function(callback, [elem, i, array])
                    else:
                        result = callback(elem, i, array)
                    if self.is_truthy(result):
                        return True
                return False
            return some_method

        if method_name == "every":
            def every_method(callback):
                for i, elem in enumerate(array.elements):
                    if isinstance(callback, JSFunction):
                        result = self.call_function(callback, [elem, i, array])
                    else:
                        result = callback(elem, i, array)
                    if not self.is_truthy(result):
                        return False
                return True
            return every_method

        return None

    def get_string_method(self, string, method_name):
        if method_name == "split":
            def split_method(separator=""):
                if separator == "":
                    return JSArray(list(string))
                return JSArray(string.split(separator))
            return split_method

        if method_name == "replace":
            def replace_method(search, replacement):
                return string.replace(str(search), str(replacement), 1)
            return replace_method

        if method_name == "replaceAll":
            def replace_all_method(search, replacement):
                return string.replace(str(search), str(replacement))
            return replace_all_method

        if method_name == "substring":
            def substring_method(start, end=None):
                start = int(start)
                if end is None:
                    return string[start:]
                return string[start:int(end)]
            return substring_method

        if method_name == "slice":
            def slice_method(start, end=None):
                start = int(start)
                if end is None:
                    return string[start:]
                return string[start:int(end)]
            return slice_method

        if method_name == "trim":
            return lambda: string.strip()

        if method_name == "toUpperCase":
            return lambda: string.upper()

        if method_name == "toLowerCase":
            return lambda: string.lower()

        if method_name == "includes":
            return lambda search: str(search) in string

        if method_name == "startsWith":
            return lambda search: string.startswith(str(search))

        if method_name == "endsWith":
            return lambda search: string.endswith(str(search))

        if method_name == "indexOf":
            def index_of_method(search):
                try:
                    return string.index(str(search))
                except ValueError:
                    return -1
            return index_of_method

        if method_name == "charAt":
            def char_at_method(index):
                index = int(index)
                if 0 <= index < len(string):
                    return string[index]
                return ""
            return char_at_method

        if method_name == "charCodeAt":
            def char_code_at_method(index):
                index = int(index)
                if 0 <= index < len(string):
                    return ord(string[index])
                return float('nan')
            return char_code_at_method

        if method_name == "concat":
            return lambda *strings: string + "".join(str(s) for s in strings)

        if method_name == "repeat":
            return lambda count: string * int(count)

        if method_name == "length":
            return len(string)

        return None
