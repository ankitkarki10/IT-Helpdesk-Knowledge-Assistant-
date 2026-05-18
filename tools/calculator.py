import ast
import operator
from core.logger import get_logger

logger = get_logger(__name__)

# Allowed operators
allowed_operators = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.BitXor: operator.xor,
    ast.USub: operator.neg
}

def evaluate_expr(node):
    if isinstance(node, ast.Constant): # <number>
        return node.value
    elif isinstance(node, ast.BinOp): # <left> <operator> <right>
        return allowed_operators[type(node.op)](evaluate_expr(node.left), evaluate_expr(node.right))
    elif isinstance(node, ast.UnaryOp): # <operator> <operand> e.g., -1
        return allowed_operators[type(node.op)](evaluate_expr(node.operand))
    else:
        raise TypeError(node)

def run_calculator(expression: str) -> str:
    """Safe evaluation of simple mathematical expressions."""
    logger.info(f"Tool execution: calculator on '{expression}'")
    try:
        # We parse the expression cleanly. For simplicity we try to use ast.parse
        node = ast.parse(expression, mode='eval').body
        result = evaluate_expr(node)
        return str(result)
    except Exception as e:
        logger.error(f"Calculator failed for expression {expression}: {e}")
        return f"Error computing {expression}"
