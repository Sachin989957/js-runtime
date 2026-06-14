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

class JSException(Exception):
    def __init__(self, value):
        self.value = value

class JSFunction:
    def __init__(self, params, body, closure_scopes):
        self.params = params
        self.body = body
        self.closure_scopes = closure_scopes  # list of scope dicts (references)

class JSObject:
    def __init__(self, properties=None):
        self.properties = properties or {}

    def get(self, key):
        return self.properties.get(str(key))

    def set(self, key, value):
        self.properties[str(key)] = value

    def has(self, key):
        return str(key) in self.properties

class JSArray:
    def __init__(self, elements=None):
        self.elements = elements if elements is not None else []

    def __repr__(self):
        return f"JSArray({self.elements})"

class Interpreter:
    def __init__(self):
        self.global_scope = self.create_global_scope()
        self.scopes = [self.global_scope]

    def create_global_scope(self):
        scope = {
            'undefined': None,
            'null': None,
            'NaN': float('nan'),
            'Infinity': float('inf'),
        }

        interp = self

        scope['console'] = JSObject({
            'log': lambda *args: print(*[interp.js_to_string(a) for a in args]),
            'error': lambda *args: print(*[interp.js_to_string(a) for a in args]),
            'warn': lambda *args: print(*[interp.js_to_string(a) for a in args]),
        })

        scope['Math'] = JSObject({
            'floor': lambda x: int(math.floor(x)),
            'ceil': lambda x: int(math.ceil(x)),
            'round': lambda x: int(round(x)),
            'abs': abs,
            'sqrt': math.sqrt,
            'pow': lambda b, e: b ** e,
            'max': lambda *args: max(args) if args else float('-inf'),
            'min': lambda *args: min(args) if args else float('inf'),
            'random': random.random,
            'log': math.log,
            'log2': math.log2,
            'log10': math.log10,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'sign': lambda x: (1 if x > 0 else -1 if x < 0 else 0),
            'trunc': lambda x: int(math.trunc(x)),
            'hypot': lambda *args: math.hypot(*args),
            'PI': math.pi,
            'E': math.e,
            'LN2': math.log(2),
            'LN10': math.log(10),
            'SQRT2': math.sqrt(2),
        })

        scope['parseInt'] = lambda s, base=10: self._parse_int(s, base)
        scope['parseFloat'] = lambda s: self._parse_float(s)
        scope['isNaN'] = lambda x: isinstance(x, float) and math.isnan(x)
        scope['isFinite'] = lambda x: isinstance(x, (int, float)) and math.isfinite(x)
        scope['Number'] = lambda x=0: self._to_number(x)
        scope['String'] = lambda x='': self.js_to_string(x)
        scope['Boolean'] = lambda x=False: self.is_truthy(x)

        scope['Array'] = JSObject({
            'isArray': lambda x: isinstance(x, JSArray),
            'from': lambda x, mapfn=None: self._array_from(x, mapfn),
            'of': lambda *args: JSArray(list(args)),
        })

        scope['String_constructor'] = JSObject({
            'fromCharCode': lambda *codes: ''.join(chr(int(c)) for c in codes)
        })

        scope['Object'] = JSObject({
            'keys': lambda obj: JSArray(list(obj.properties.keys())) if isinstance(obj, JSObject) else JSArray([]),
            'values': lambda obj: JSArray(list(obj.properties.values())) if isinstance(obj, JSObject) else JSArray([]),
            'entries': lambda obj: JSArray([JSArray([k, v]) for k, v in obj.properties.items()]) if isinstance(obj, JSObject) else JSArray([]),
            'assign': self._object_assign,
            'create': lambda proto: JSObject({}),
        })

        scope['JSON'] = JSObject({
            'stringify': lambda val, *args: self._json_stringify(val),
            'parse': lambda s: self._json_parse(s),
        })

        scope['Date'] = self._create_date_class()

        return scope

    def _parse_int(self, s, base=10):
        try:
            if isinstance(s, (int, float)):
                return int(s)
            s = str(s).strip()
            if not s:
                return float('nan')
            # extract leading integer chars
            import re
            m = re.match(r'^[+-]?[0-9a-fA-F]+', s)
            if m:
                return int(m.group(), int(base) if base else 10)
            return float('nan')
        except:
            return float('nan')

    def _parse_float(self, s):
        try:
            if isinstance(s, (int, float)):
                return float(s)
            s = str(s).strip()
            import re
            m = re.match(r'^[+-]?[0-9]*\.?[0-9]+([eE][+-]?[0-9]+)?', s)
            if m:
                return float(m.group())
            return float('nan')
        except:
            return float('nan')

    def _to_number(self, x):
        if isinstance(x, bool):
            return 1 if x else 0
        if isinstance(x, (int, float)):
            return x
        if x is None:
            return 0
        try:
            return float(str(x))
        except:
            return float('nan')

    def _array_from(self, x, mapfn=None):
        if isinstance(x, JSArray):
            elems = list(x.elements)
        elif isinstance(x, str):
            elems = list(x)
        elif isinstance(x, JSObject):
            length = x.get('length')
            if length is not None:
                elems = [x.get(str(i)) for i in range(int(length))]
            else:
                elems = []
        else:
            elems = []
        if mapfn:
            result = []
            for i, e in enumerate(elems):
                if isinstance(mapfn, JSFunction):
                    result.append(self.call_function(mapfn, [e, i]))
                else:
                    result.append(mapfn(e, i))
            return JSArray(result)
        return JSArray(elems)

    def _object_assign(self, target, *sources):
        if not isinstance(target, JSObject):
            return target
        for src in sources:
            if isinstance(src, JSObject):
                for k, v in src.properties.items():
                    target.set(k, v)
        return target

    def _json_stringify(self, val):
        def to_json(v):
            if v is None:
                return 'null'
            if isinstance(v, bool):
                return 'true' if v else 'false'
            if isinstance(v, float):
                if v.is_integer():
                    return str(int(v))
                return str(v)
            if isinstance(v, int):
                return str(v)
            if isinstance(v, str):
                import json
                return json.dumps(v)
            if isinstance(v, JSArray):
                return '[' + ','.join(to_json(e) for e in v.elements) + ']'
            if isinstance(v, JSObject):
                pairs = [f'"{k}":{to_json(val)}' for k, val in v.properties.items()]
                return '{' + ','.join(pairs) + '}'
            return 'null'
        return to_json(val)

    def _json_parse(self, s):
        import json
        def from_json(v):
            if isinstance(v, list):
                return JSArray([from_json(e) for e in v])
            if isinstance(v, dict):
                return JSObject({k: from_json(val) for k, val in v.items()})
            return v
        return from_json(json.loads(s))

    def _create_date_class(self):
        interp = self
        def date_constructor(*args):
            now = datetime.now()
            obj = JSObject({
                'getFullYear': lambda: now.year,
                'getMonth': lambda: now.month - 1,
                'getDate': lambda: now.day,
                'getDay': lambda: now.weekday(),
                'getHours': lambda: now.hour,
                'getMinutes': lambda: now.minute,
                'getSeconds': lambda: now.second,
                'getMilliseconds': lambda: now.microsecond // 1000,
                'getTime': lambda: int(now.timestamp() * 1000),
                'toISOString': lambda: now.isoformat() + 'Z',
                'toString': lambda: str(now),
            })
            return obj
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
        return None  # undefined rather than error

    def set_variable(self, name, value):
        for scope in reversed(self.scopes):
            if name in scope:
                scope[name] = value
                return
        self.scopes[0][name] = value  # global

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
            return "function() { [native code] }"
        if isinstance(value, float):
            if math.isnan(value):
                return "NaN"
            if math.isinf(value):
                return "Infinity" if value > 0 else "-Infinity"
            if value.is_integer():
                return str(int(value))
            return str(value)
        if isinstance(value, int):
            return str(value)
        return str(value)

    def is_truthy(self, value):
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0 and not (isinstance(value, float) and math.isnan(value))
        if isinstance(value, str):
            return value != ""
        return True

    def interpret(self, program):
        for stmt in program:
            self.execute(stmt)

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

        if isinstance(node, TemplateLiteralNode):
            parts = []
            for is_expr, val in node.parts:
                if is_expr:
                    parts.append(self.js_to_string(self.execute(val)))
                else:
                    parts.append(val)
            return "".join(parts)

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

        if isinstance(node, VarNode):
            value = self.execute(node.value)
            # var is function-scoped, define at current scope
            self.define_variable(node.name, value)
            return value

        if isinstance(node, AssignmentNode):
            return self.execute_assignment(node)

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
            if node.init:
                self.execute(node.init)
            result = None
            while node.condition is None or self.is_truthy(self.execute(node.condition)):
                try:
                    result = self.execute(node.body)
                except BreakException:
                    break
                except ContinueException:
                    pass
                if node.update:
                    self.execute(node.update)
            self.pop_scope()
            return result

        if isinstance(node, ForOfNode):
            self.push_scope()
            iterable = self.execute(node.iterable)
            if isinstance(iterable, JSArray):
                items = iterable.elements
            elif isinstance(iterable, str):
                items = list(iterable)
            else:
                items = []
            for item in items:
                self.define_variable(node.var_name, item)
                try:
                    self.execute(node.body)
                except BreakException:
                    break
                except ContinueException:
                    continue
            self.pop_scope()
            return None

        if isinstance(node, ForInNode):
            self.push_scope()
            iterable = self.execute(node.iterable)
            if isinstance(iterable, JSObject):
                keys = list(iterable.properties.keys())
            elif isinstance(iterable, JSArray):
                keys = [str(i) for i in range(len(iterable.elements))]
            else:
                keys = []
            for key in keys:
                self.define_variable(node.var_name, key)
                try:
                    self.execute(node.body)
                except BreakException:
                    break
                except ContinueException:
                    continue
            self.pop_scope()
            return None

        if isinstance(node, SwitchNode):
            val = self.execute(node.expression)
            matched = False
            try:
                for case_val_node, stmts in node.cases:
                    case_val = self.execute(case_val_node)
                    if not matched and self.strict_equal(val, case_val):
                        matched = True
                    if matched:
                        for stmt in stmts:
                            self.execute(stmt)
                if not matched and node.default is not None:
                    for stmt in node.default:
                        self.execute(stmt)
            except BreakException:
                pass
            return None

        if isinstance(node, BlockNode):
            self.push_scope()
            result = None
            try:
                for stmt in node.statements:
                    result = self.execute(stmt)
            finally:
                self.pop_scope()
            return result

        if isinstance(node, FunctionNode):
            closure_scopes = list(self.scopes)  # references to actual scope dicts
            func = JSFunction(node.params, node.body, closure_scopes)
            if node.name:
                self.define_variable(node.name, func)
            return func

        if isinstance(node, ArrowFunctionNode):
            closure_scopes = list(self.scopes)  # references to actual scope dicts
            return JSFunction(node.params, node.body, closure_scopes)

        if isinstance(node, FunctionCallNode):
            return self.execute_function_call(node)

        if isinstance(node, NewNode):
            return self.execute_new(node)

        if isinstance(node, ReturnNode):
            value = self.execute(node.value) if node.value else None
            raise ReturnException(value)

        if isinstance(node, BreakNode):
            raise BreakException()

        if isinstance(node, ContinueNode):
            raise ContinueException()

        if isinstance(node, ThrowNode):
            value = self.execute(node.value)
            raise JSException(value)

        if isinstance(node, TryCatchNode):
            try:
                self.execute(node.try_block)
            except JSException as e:
                if node.catch_block:
                    self.push_scope()
                    if node.catch_var:
                        self.define_variable(node.catch_var, e.value)
                    self.execute(node.catch_block)
                    self.pop_scope()
            except Exception as e:
                if node.catch_block:
                    self.push_scope()
                    if node.catch_var:
                        self.define_variable(node.catch_var, str(e))
                    self.execute(node.catch_block)
                    self.pop_scope()
            finally:
                if node.finally_block:
                    self.execute(node.finally_block)
            return None

        if isinstance(node, ArrayNode):
            elements = []
            for elem in node.elements:
                if isinstance(elem, SpreadNode):
                    spread_val = self.execute(elem.expression)
                    if isinstance(spread_val, JSArray):
                        elements.extend(spread_val.elements)
                    elif isinstance(spread_val, str):
                        elements.extend(list(spread_val))
                else:
                    elements.append(self.execute(elem))
            return JSArray(elements)

        if isinstance(node, ObjectNode):
            properties = {}
            for key, value in node.properties.items():
                properties[key] = self.execute(value)
            return JSObject(properties)

        if isinstance(node, ArrayAccessNode):
            array = self.execute(node.array_node)
            index = self.execute(node.index)
            if isinstance(array, JSArray):
                idx = int(float(index))
                if idx < 0:
                    idx = len(array.elements) + idx
                if 0 <= idx < len(array.elements):
                    return array.elements[idx]
                return None
            if isinstance(array, str):
                if isinstance(index, (int, float)):
                    idx = int(index)
                    if 0 <= idx < len(array):
                        return array[idx]
                return None
            if isinstance(array, JSObject):
                return array.get(str(index))
            return None

        if isinstance(node, MemberAccessNode):
            return self.execute_member_access(node)

        if isinstance(node, TernaryOpNode):
            condition = self.execute(node.condition)
            if self.is_truthy(condition):
                return self.execute(node.then_expr)
            else:
                return self.execute(node.else_expr)

        return None

    def execute_assignment(self, node):
        value = self.execute(node.value)
        target = node.target
        if isinstance(target, VariableNode):
            self.set_variable(target.name, value)
        elif isinstance(target, MemberAccessNode):
            obj = self.execute(target.object_node)
            prop = target.property_name
            if isinstance(obj, JSObject):
                obj.set(prop, value)
            elif isinstance(obj, JSArray):
                try:
                    idx = int(float(prop))
                    while idx >= len(obj.elements):
                        obj.elements.append(None)
                    obj.elements[idx] = value
                except:
                    pass
        elif isinstance(target, ArrayAccessNode):
            obj = self.execute(target.array_node)
            index = self.execute(target.index)
            if isinstance(obj, JSArray):
                idx = int(float(index))
                while idx >= len(obj.elements):
                    obj.elements.append(None)
                obj.elements[idx] = value
            elif isinstance(obj, JSObject):
                obj.set(str(index), value)
        return value

    def execute_member_access(self, node):
        obj = self.execute(node.object_node)
        prop = node.property_name

        if obj is None:
            return None

        if isinstance(obj, JSArray):
            if prop == 'length':
                return len(obj.elements)
            method = self.get_array_method(obj, prop)
            if method is not None:
                return method
            # numeric string access
            try:
                idx = int(prop)
                if 0 <= idx < len(obj.elements):
                    return obj.elements[idx]
            except:
                pass
            return None

        if isinstance(obj, str):
            if prop == 'length':
                return len(obj)
            method = self.get_string_method(obj, prop)
            if method is not None:
                return method
            return None

        if isinstance(obj, JSObject):
            val = obj.get(prop)
            return val

        if isinstance(obj, dict):
            return obj.get(prop)

        if isinstance(obj, (int, float)):
            # Number methods
            if prop == 'toFixed':
                return lambda digits=0: format(obj, f'.{int(digits)}f')
            if prop == 'toString':
                return lambda base=10: self._number_to_string(obj, int(base))
            return None

        return None

    def _number_to_string(self, n, base=10):
        if base == 10:
            return self.js_to_string(n)
        if isinstance(n, float) and n.is_integer():
            n = int(n)
        return format(int(n), 'b' if base == 2 else 'o' if base == 8 else 'x' if base == 16 else 'd')

    def execute_function_call(self, node):
        if isinstance(node.name, MemberAccessNode):
            obj = self.execute(node.name.object_node)
            method_name = node.name.property_name

            # Evaluate args with spread support
            args = self._eval_args(node.args)

            if isinstance(obj, JSArray):
                method = self.get_array_method(obj, method_name)
                if method is not None:
                    return method(*args)

            if isinstance(obj, str):
                method = self.get_string_method(obj, method_name)
                if method is not None:
                    if callable(method) and not isinstance(method, JSFunction):
                        return method(*args)
                    if isinstance(method, JSFunction):
                        return self.call_function(method, args)

            if isinstance(obj, JSObject):
                method = obj.get(method_name)
                if method is None and method_name == 'hasOwnProperty':
                    key = args[0] if args else None
                    return obj.has(str(key)) if key is not None else False
                if isinstance(method, JSFunction):
                    return self.call_function(method, args, this_obj=obj)
                if callable(method):
                    return method(*args)

            if isinstance(obj, dict):
                method = obj.get(method_name)
                if callable(method):
                    return method(*args)

            return None

        # Regular function call
        func = self.execute(node.name)
        args = self._eval_args(node.args)

        if isinstance(func, JSFunction):
            return self.call_function(func, args)

        if callable(func):
            return func(*args)

        return None

    def _eval_args(self, arg_nodes):
        args = []
        for arg in arg_nodes:
            if isinstance(arg, SpreadNode):
                val = self.execute(arg.expression)
                if isinstance(val, JSArray):
                    args.extend(val.elements)
                elif isinstance(val, str):
                    args.extend(list(val))
                else:
                    args.append(val)
            else:
                args.append(self.execute(arg))
        return args

    def execute_new(self, node):
        constructor_name = node.constructor.name if isinstance(node.constructor, VariableNode) else None
        args = self._eval_args(node.args)

        if constructor_name == 'Date':
            date_ctor = self.get_variable('Date')
            if callable(date_ctor):
                return date_ctor(*args)

        if constructor_name == 'Array':
            if len(args) == 1 and isinstance(args[0], (int, float)):
                return JSArray([None] * int(args[0]))
            return JSArray(args)

        if constructor_name == 'Object':
            return JSObject({})

        if constructor_name == 'Error' or constructor_name == 'TypeError':
            msg = args[0] if args else ''
            obj = JSObject({'message': msg, 'name': constructor_name or 'Error'})
            return obj

        # Try user-defined constructor
        func = self.get_variable(constructor_name) if constructor_name else None
        if isinstance(func, JSFunction):
            obj = JSObject({})
            return self.call_function(func, args, this_obj=obj)

        return JSObject({})

    def execute_binary_op(self, node):
        # Postfix ops stored as BinaryOpNode with None right
        if node.op in ("++_post", "--_post"):
            delta = 1 if node.op == "++_post" else -1
            if isinstance(node.left, VariableNode):
                val = self.get_variable(node.left.name)
                self.set_variable(node.left.name, val + delta)
                return val
            elif isinstance(node.left, MemberAccessNode):
                obj = self.execute(node.left.object_node)
                prop = node.left.property_name
                if isinstance(obj, JSObject):
                    val = obj.get(prop)
                    if val is None: val = 0
                    obj.set(prop, val + delta)
                    return val
                elif isinstance(obj, JSArray):
                    try:
                        idx = int(prop)
                        val = obj.elements[idx]
                        obj.elements[idx] = val + delta
                        return val
                    except:
                        pass
            elif isinstance(node.left, ArrayAccessNode):
                arr = self.execute(node.left.array_node)
                idx = int(self.execute(node.left.index))
                if isinstance(arr, JSArray):
                    val = arr.elements[idx]
                    arr.elements[idx] = val + delta
                    return val
            return self.execute(node.left)

        left = self.execute(node.left)
        right = self.execute(node.right)

        if node.op == "+":
            if isinstance(left, str) or isinstance(right, str):
                return self.js_to_string(left) + self.js_to_string(right)
            if isinstance(left, bool):
                left = 1 if left else 0
            if isinstance(right, bool):
                right = 1 if right else 0
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left + right
            return self.js_to_string(left) + self.js_to_string(right)

        if node.op == "-":
            return self._to_number(left) - self._to_number(right)

        if node.op == "*":
            return self._to_number(left) * self._to_number(right)

        if node.op == "/":
            r = self._to_number(right)
            l = self._to_number(left)
            if r == 0:
                if l == 0: return float('nan')
                return float('inf') if l > 0 else float('-inf')
            return l / r

        if node.op == "%":
            r = self._to_number(right)
            l = self._to_number(left)
            if r == 0: return float('nan')
            return l % r

        if node.op == "**":
            return self._to_number(left) ** self._to_number(right)

        if node.op == "==":
            return self.loose_equal(left, right)

        if node.op == "!=":
            return not self.loose_equal(left, right)

        if node.op == "===":
            return self.strict_equal(left, right)

        if node.op == "!==":
            return not self.strict_equal(left, right)

        if node.op == "<":
            return self._compare(left, right) < 0

        if node.op == ">":
            return self._compare(left, right) > 0

        if node.op == "<=":
            return self._compare(left, right) <= 0

        if node.op == ">=":
            return self._compare(left, right) >= 0

        if node.op == "&&":
            if not self.is_truthy(left):
                return left
            return right

        if node.op == "||":
            if self.is_truthy(left):
                return left
            return right

        if node.op == "&":
            return int(self._to_number(left)) & int(self._to_number(right))

        if node.op == "|":
            return int(self._to_number(left)) | int(self._to_number(right))

        if node.op == "^":
            return int(self._to_number(left)) ^ int(self._to_number(right))

        if node.op == "<<":
            return int(self._to_number(left)) << (int(self._to_number(right)) & 31)

        if node.op == ">>":
            return int(self._to_number(left)) >> (int(self._to_number(right)) & 31)

        if node.op == ">>>":
            return (int(self._to_number(left)) & 0xFFFFFFFF) >> (int(self._to_number(right)) & 31)

        if node.op == "instanceof":
            return False  # simplified

        if node.op == "in":
            if isinstance(right, JSObject):
                return right.has(str(left))
            if isinstance(right, JSArray):
                try:
                    return 0 <= int(float(str(left))) < len(right.elements)
                except:
                    return False
            return False

        raise Exception(f"Unknown binary operator: {node.op}")

    def _compare(self, left, right):
        if isinstance(left, str) and isinstance(right, str):
            return (left > right) - (left < right)
        l = self._to_number(left)
        r = self._to_number(right)
        return (l > r) - (l < r)

    def execute_unary_op(self, node):
        if node.op == "typeof":
            # Special: don't error on undefined vars
            if isinstance(node.operand, VariableNode):
                val = self.get_variable(node.operand.name)
            else:
                val = self.execute(node.operand)
            if val is None:
                return "undefined"
            if isinstance(val, bool):
                return "boolean"
            if isinstance(val, (int, float)):
                return "number"
            if isinstance(val, str):
                return "string"
            if isinstance(val, JSFunction):
                return "function"
            if callable(val):
                return "function"
            return "object"

        operand = self.execute(node.operand)

        if node.op == "!":
            return not self.is_truthy(operand)

        if node.op == "-":
            return -self._to_number(operand)

        if node.op == "+":
            return self._to_number(operand)

        if node.op == "~":
            return ~int(self._to_number(operand))

        if node.op == "++":
            new_val = self._to_number(operand) + 1
            if isinstance(node.operand, VariableNode):
                self.set_variable(node.operand.name, new_val)
            elif isinstance(node.operand, MemberAccessNode):
                obj = self.execute(node.operand.object_node)
                if isinstance(obj, JSObject):
                    obj.set(node.operand.property_name, new_val)
            return new_val

        if node.op == "--":
            new_val = self._to_number(operand) - 1
            if isinstance(node.operand, VariableNode):
                self.set_variable(node.operand.name, new_val)
            elif isinstance(node.operand, MemberAccessNode):
                obj = self.execute(node.operand.object_node)
                if isinstance(obj, JSObject):
                    obj.set(node.operand.property_name, new_val)
            return new_val

        raise Exception(f"Unknown unary operator: {node.op}")

    def strict_equal(self, left, right):
        if type(left) != type(right):
            # bool vs int/float edge case
            if isinstance(left, bool) or isinstance(right, bool):
                return False
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left == right
            return False
        if left is None:
            return right is None
        return left == right

    def loose_equal(self, left, right):
        if left is None and right is None:
            return True
        if left is None or right is None:
            return False
        if type(left) == type(right):
            return left == right
        if isinstance(left, bool):
            left = 1 if left else 0
        if isinstance(right, bool):
            right = 1 if right else 0
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

    def call_function(self, func, args, this_obj=None):
        # Save and replace scope stack with closure scopes + new scope
        saved_scopes = self.scopes
        new_scope = {}
        self.scopes = list(func.closure_scopes) + [new_scope]

        # Bind 'this'
        if this_obj is not None:
            new_scope['this'] = this_obj

        # Bind params
        param_idx = 0
        for param in func.params:
            if param.startswith("..."):
                rest_name = param[3:]
                new_scope[rest_name] = JSArray(args[param_idx:])
                param_idx = len(args)
            else:
                new_scope[param] = args[param_idx] if param_idx < len(args) else None
                param_idx += 1

        try:
            self.execute(func.body)
            result = None
        except ReturnException as e:
            result = e.value

        self.scopes = saved_scopes
        return result

    def get_array_method(self, array, method_name):
        if method_name == "push":
            def push_method(*items):
                array.elements.extend(items)
                return len(array.elements)
            return push_method

        if method_name == "pop":
            return lambda: array.elements.pop() if array.elements else None

        if method_name == "shift":
            return lambda: array.elements.pop(0) if array.elements else None

        if method_name == "unshift":
            def unshift_method(*items):
                for item in reversed(items):
                    array.elements.insert(0, item)
                return len(array.elements)
            return unshift_method

        if method_name == "slice":
            def slice_method(start=0, end=None):
                s = int(start) if start is not None else 0
                if s < 0: s = max(0, len(array.elements) + s)
                if end is None:
                    return JSArray(list(array.elements[s:]))
                e = int(end)
                if e < 0: e = max(0, len(array.elements) + e)
                return JSArray(list(array.elements[s:e]))
            return slice_method

        if method_name == "splice":
            def splice_method(start, delete_count=None, *items):
                s = int(start)
                if s < 0: s = max(0, len(array.elements) + s)
                if delete_count is None:
                    delete_count = len(array.elements) - s
                dc = int(delete_count)
                removed = JSArray(list(array.elements[s:s + dc]))
                array.elements[s:s + dc] = list(items)
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
                if sep is None: sep = ","
                return sep.join(self.js_to_string(elem) for elem in array.elements)
            return join_method

        if method_name == "reverse":
            def reverse_method():
                array.elements.reverse()
                return array
            return reverse_method

        if method_name == "sort":
            def sort_method(compare_fn=None):
                if compare_fn is None:
                    array.elements.sort(key=lambda x: self.js_to_string(x))
                else:
                    import functools
                    def cmp(a, b):
                        if isinstance(compare_fn, JSFunction):
                            r = self.call_function(compare_fn, [a, b])
                        else:
                            r = compare_fn(a, b)
                        if r is None: return 0
                        return int(r) if isinstance(r, (int, float)) else 0
                    array.elements.sort(key=functools.cmp_to_key(cmp))
                return array
            return sort_method

        if method_name == "includes":
            def includes_method(item, from_index=0):
                for elem in array.elements:
                    if self.strict_equal(elem, item):
                        return True
                return False
            return includes_method

        if method_name == "indexOf":
            def index_of_method(item, from_index=0):
                for i, elem in enumerate(array.elements):
                    if i < int(from_index): continue
                    if self.strict_equal(elem, item):
                        return i
                return -1
            return index_of_method

        if method_name == "lastIndexOf":
            def last_index_of_method(item):
                for i in range(len(array.elements) - 1, -1, -1):
                    if self.strict_equal(array.elements[i], item):
                        return i
                return -1
            return last_index_of_method

        if method_name == "flat":
            def flat_method(depth=1):
                def flatten(arr, d):
                    result = []
                    for elem in arr:
                        if isinstance(elem, JSArray) and d > 0:
                            result.extend(flatten(elem.elements, d - 1))
                        else:
                            result.append(elem)
                    return result
                return JSArray(flatten(array.elements, int(depth)))
            return flat_method

        if method_name == "flatMap":
            def flat_map_method(callback):
                result = []
                for i, elem in enumerate(array.elements):
                    if isinstance(callback, JSFunction):
                        val = self.call_function(callback, [elem, i, array])
                    else:
                        val = callback(elem, i, array)
                    if isinstance(val, JSArray):
                        result.extend(val.elements)
                    else:
                        result.append(val)
                return JSArray(result)
            return flat_map_method

        if method_name == "forEach":
            def for_each_method(callback):
                for i, elem in enumerate(array.elements):
                    if isinstance(callback, JSFunction):
                        self.call_function(callback, [elem, i, array])
                    else:
                        callback(elem, i, array)
                return None
            return for_each_method

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
                        ok = self.call_function(callback, [elem, i, array])
                    else:
                        ok = callback(elem, i, array)
                    if self.is_truthy(ok):
                        result.append(elem)
                return JSArray(result)
            return filter_method

        if method_name == "reduce":
            def reduce_method(callback, initial=None):
                elems = array.elements
                if len(elems) == 0 and initial is None:
                    raise Exception("Reduce of empty array with no initial value")
                start_idx = 0
                if initial is None:
                    accumulator = elems[0]
                    start_idx = 1
                else:
                    accumulator = initial
                for i in range(start_idx, len(elems)):
                    if isinstance(callback, JSFunction):
                        accumulator = self.call_function(callback, [accumulator, elems[i], i, array])
                    else:
                        accumulator = callback(accumulator, elems[i], i, array)
                return accumulator
            return reduce_method

        if method_name == "reduceRight":
            def reduce_right_method(callback, initial=None):
                elems = array.elements
                if len(elems) == 0 and initial is None:
                    raise Exception("Reduce of empty array with no initial value")
                if initial is None:
                    accumulator = elems[-1]
                    indices = range(len(elems) - 2, -1, -1)
                else:
                    accumulator = initial
                    indices = range(len(elems) - 1, -1, -1)
                for i in indices:
                    if isinstance(callback, JSFunction):
                        accumulator = self.call_function(callback, [accumulator, elems[i], i, array])
                    else:
                        accumulator = callback(accumulator, elems[i], i, array)
                return accumulator
            return reduce_right_method

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

        if method_name == "findIndex":
            def find_index_method(callback):
                for i, elem in enumerate(array.elements):
                    if isinstance(callback, JSFunction):
                        found = self.call_function(callback, [elem, i, array])
                    else:
                        found = callback(elem, i, array)
                    if self.is_truthy(found):
                        return i
                return -1
            return find_index_method

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

        if method_name == "fill":
            def fill_method(value, start=0, end=None):
                s = int(start)
                e = int(end) if end is not None else len(array.elements)
                for i in range(s, e):
                    if 0 <= i < len(array.elements):
                        array.elements[i] = value
                return array
            return fill_method

        if method_name == "keys":
            return lambda: JSArray(list(range(len(array.elements))))

        if method_name == "values":
            return lambda: JSArray(list(array.elements))

        if method_name == "entries":
            return lambda: JSArray([JSArray([i, e]) for i, e in enumerate(array.elements)])

        if method_name == "toString":
            return lambda: ",".join(self.js_to_string(e) for e in array.elements)

        if method_name == "length":
            return len(array.elements)

        return None

    def get_string_method(self, string, method_name):
        if method_name == "split":
            def split_method(separator=None, limit=None):
                if separator is None:
                    return JSArray([string])
                if separator == "":
                    result = list(string)
                else:
                    result = string.split(str(separator))
                if limit is not None:
                    result = result[:int(limit)]
                return JSArray(result)
            return split_method

        if method_name == "replace":
            def replace_method(search, replacement):
                if isinstance(replacement, str):
                    return string.replace(str(search), replacement, 1)
                return string.replace(str(search), str(replacement), 1)
            return replace_method

        if method_name == "replaceAll":
            def replace_all_method(search, replacement):
                return string.replace(str(search), str(replacement))
            return replace_all_method

        if method_name == "substring":
            def substring_method(start, end=None):
                s = max(0, int(start))
                if end is None:
                    return string[s:]
                e = max(0, int(end))
                if s > e:
                    s, e = e, s
                return string[s:e]
            return substring_method

        if method_name == "slice":
            def slice_method(start=0, end=None):
                s = int(start)
                if end is None:
                    return string[s:]
                return string[s:int(end)]
            return slice_method

        if method_name == "substr":
            def substr_method(start, length=None):
                s = int(start)
                if s < 0: s = max(0, len(string) + s)
                if length is None:
                    return string[s:]
                return string[s:s + int(length)]
            return substr_method

        if method_name == "trim":
            return lambda: string.strip()

        if method_name == "trimStart" or method_name == "trimLeft":
            return lambda: string.lstrip()

        if method_name == "trimEnd" or method_name == "trimRight":
            return lambda: string.rstrip()

        if method_name == "toUpperCase":
            return lambda: string.upper()

        if method_name == "toLowerCase":
            return lambda: string.lower()

        if method_name == "includes":
            def includes_method(search, pos=0):
                return str(search) in string[int(pos):]
            return includes_method

        if method_name == "startsWith":
            def starts_with_method(search, pos=0):
                return string[int(pos):].startswith(str(search))
            return starts_with_method

        if method_name == "endsWith":
            def ends_with_method(search, end_pos=None):
                s = string if end_pos is None else string[:int(end_pos)]
                return s.endswith(str(search))
            return ends_with_method

        if method_name == "indexOf":
            def index_of_method(search, from_index=0):
                try:
                    return string.index(str(search), int(from_index))
                except ValueError:
                    return -1
            return index_of_method

        if method_name == "lastIndexOf":
            def last_index_of_method(search):
                try:
                    return string.rindex(str(search))
                except ValueError:
                    return -1
            return last_index_of_method

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

        if method_name == "codePointAt":
            def code_point_at_method(index):
                index = int(index)
                if 0 <= index < len(string):
                    return ord(string[index])
                return None
            return code_point_at_method

        if method_name == "concat":
            return lambda *strings: string + "".join(str(s) for s in strings)

        if method_name == "repeat":
            return lambda count: string * int(count)

        if method_name == "padStart":
            def pad_start_method(target_length, pad_str=" "):
                return string.rjust(int(target_length), str(pad_str)[0] if pad_str else " ")
            return pad_start_method

        if method_name == "padEnd":
            def pad_end_method(target_length, pad_str=" "):
                return string.ljust(int(target_length), str(pad_str)[0] if pad_str else " ")
            return pad_end_method

        if method_name == "at":
            def at_method(index):
                idx = int(index)
                if idx < 0: idx = len(string) + idx
                if 0 <= idx < len(string):
                    return string[idx]
                return None
            return at_method

        if method_name == "length":
            return len(string)

        if method_name == "toString" or method_name == "valueOf":
            return lambda: string

        return None