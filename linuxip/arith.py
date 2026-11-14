"""Shell arithmetic for $((...)): integers, + - * / % **, comparisons, && || !, ( ), variables."""
import ast
import operator

from .core import ShellError

BINARY = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Pow: operator.pow,
          ast.BitAnd: operator.and_, ast.BitOr: operator.or_, ast.BitXor: operator.xor,
          ast.LShift: operator.lshift, ast.RShift: operator.rshift}
COMPARE = {ast.Eq: operator.eq, ast.NotEq: operator.ne, ast.Lt: operator.lt, ast.LtE: operator.le,
           ast.Gt: operator.gt, ast.GtE: operator.ge}


def evaluate(expr, env):
    """Evaluate a bash arithmetic expression to an int (unset variables are 0)."""
    text = expr.strip().replace("&&", " and ").replace("||", " or ").replace("$", "")
    if not text:
        return 0
    try:
        tree = ast.parse(text, mode="eval")
    except SyntaxError:
        raise ShellError(f"bash: {expr.strip()}: syntax error in expression (error token is \"{expr.strip()}\")", 1)

    def value(name):
        raw = env.get(name, "0") or "0"
        try:
            return int(raw)
        except ValueError:
            return 0

    def walk(n):
        if isinstance(n, ast.Expression):
            return walk(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, int):
            return int(n.value)
        if isinstance(n, ast.Name):
            return value(n.id)
        if isinstance(n, ast.UnaryOp):
            v = walk(n.operand)
            if isinstance(n.op, ast.USub):
                return -v
            if isinstance(n.op, ast.UAdd):
                return v
            if isinstance(n.op, ast.Not):
                return 0 if v else 1
            if isinstance(n.op, ast.Invert):
                return ~v
        if isinstance(n, ast.BinOp):
            a, b = walk(n.left), walk(n.right)
            if isinstance(n.op, (ast.Div, ast.FloorDiv)):
                if b == 0:
                    raise ShellError("bash: division by 0 (error token is \"0\")", 1)
                q = abs(a) // abs(b)          # bash truncates toward zero
                return q if (a >= 0) == (b >= 0) else -q
            if isinstance(n.op, ast.Mod):
                if b == 0:
                    raise ShellError("bash: division by 0 (error token is \"0\")", 1)
                return int(a - b * (abs(a) // abs(b)) * (1 if (a >= 0) == (b >= 0) else -1))
            if type(n.op) in BINARY:
                return int(BINARY[type(n.op)](a, b))
        if isinstance(n, ast.BoolOp):
            vals = [walk(v) for v in n.values]
            return int(all(vals)) if isinstance(n.op, ast.And) else int(any(vals))
        if isinstance(n, ast.Compare) and len(n.ops) == 1 and type(n.ops[0]) in COMPARE:
            return int(COMPARE[type(n.ops[0])](walk(n.left), walk(n.comparators[0])))
        if isinstance(n, ast.IfExp):
            return walk(n.body) if walk(n.test) else walk(n.orelse)
        raise ShellError(f"bash: {expr.strip()}: syntax error in expression", 1)
    return walk(tree)
