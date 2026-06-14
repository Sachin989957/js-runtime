class NumberNode:
    def __init__(self, value):
        self.value = value

class StringNode:
    def __init__(self, value):
        self.value = value

class BooleanNode:
    def __init__(self, value):
        self.value = value

class NullNode:
    pass

class UndefinedNode:
    pass

class VariableNode:
    def __init__(self, name):
        self.name = name

class BinaryOpNode:
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class UnaryOpNode:
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand

class LetNode:
    def __init__(self, name, value):
        self.name = name
        self.value = value

class ConstNode:
    def __init__(self, name, value):
        self.name = name
        self.value = value

class VarNode:
    def __init__(self, name, value):
        self.name = name
        self.value = value

class ConsoleLogNode:
    def __init__(self, expression):
        self.expression = expression

class IfNode:
    def __init__(self, condition, then_block, else_block=None):
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block

class WhileNode:
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class DoWhileNode:
    def __init__(self, body, condition):
        self.body = body
        self.condition = condition

class ForNode:
    def __init__(self, init, condition, update, body):
        self.init = init
        self.condition = condition
        self.update = update
        self.body = body

class ForInNode:
    def __init__(self, var_type, var_name, iterable, body):
        self.var_type = var_type
        self.var_name = var_name
        self.iterable = iterable
        self.body = body

class ForOfNode:
    def __init__(self, var_type, var_name, iterable, body):
        self.var_type = var_type
        self.var_name = var_name
        self.iterable = iterable
        self.body = body

class SwitchNode:
    def __init__(self, expression, cases, default):
        self.expression = expression
        self.cases = cases  # list of (value, body_stmts)
        self.default = default  # list of stmts or None

class FunctionNode:
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body

class FunctionCallNode:
    def __init__(self, name, args):
        self.name = name
        self.args = args

class ArrayNode:
    def __init__(self, elements):
        self.elements = elements

class ObjectNode:
    def __init__(self, properties):
        self.properties = properties

class MemberAccessNode:
    def __init__(self, object_node, property_name):
        self.object_node = object_node
        self.property_name = property_name

class ArrayAccessNode:
    def __init__(self, array_node, index):
        self.array_node = array_node
        self.index = index

class AssignmentNode:
    def __init__(self, target, value):
        self.target = target
        self.value = value

class BreakNode:
    pass

class ContinueNode:
    pass

class ReturnNode:
    def __init__(self, value=None):
        self.value = value

class ThrowNode:
    def __init__(self, value):
        self.value = value

class TryCatchNode:
    def __init__(self, try_block, catch_var, catch_block, finally_block):
        self.try_block = try_block
        self.catch_var = catch_var
        self.catch_block = catch_block
        self.finally_block = finally_block

class BlockNode:
    def __init__(self, statements):
        self.statements = statements

class SpreadNode:
    def __init__(self, expression):
        self.expression = expression

class ArrowFunctionNode:
    def __init__(self, params, body):
        self.params = params
        self.body = body

class NewNode:
    def __init__(self, constructor, args):
        self.constructor = constructor
        self.args = args

class TemplateLiteralNode:
    def __init__(self, parts):
        # parts: list of (is_expr, value) - is_expr True means evaluate, False means raw string
        self.parts = parts

class TernaryOpNode:
    def __init__(self, condition, then_expr, else_expr):
        self.condition = condition
        self.then_expr = then_expr
        self.else_expr = else_expr