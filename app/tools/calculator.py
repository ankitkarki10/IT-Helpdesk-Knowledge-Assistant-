"""Safe calculator tool using ast."""

import ast
import operator
from typing import Union
from app.core.config import get_logger

logger = get_logger(__name__)


class Calculator:
    """Safe calculator tool for mathematical expressions."""
    
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }
    
    @staticmethod
    def _evaluate_node(node: ast.expr) -> Union[int, float]:
        """Safely evaluate an AST node."""
        if isinstance(node, ast.Constant):
            if not isinstance(node.value, (int, float)):
                raise ValueError(f"Unsupported constant type: {type(node.value)}")
            return node.value
        elif isinstance(node, ast.BinOp):
            left = Calculator._evaluate_node(node.left)
            right = Calculator._evaluate_node(node.right)
            op = Calculator.OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operator: {type(node.op)}")
            return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = Calculator._evaluate_node(node.operand)
            op = Calculator.OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operator: {type(node.op)}")
            return op(operand)
        else:
            raise ValueError(f"Unsupported node type: {type(node)}")
    
    @staticmethod
    def evaluate(expression: str) -> Union[int, float]:
        """
        Safely evaluate a mathematical expression.
        
        Args:
            expression: Mathematical expression string
            
        Returns:
            Result of evaluation
            
        Raises:
            ValueError: If expression is invalid or unsafe
        """
        try:
            # Parse the expression
            tree = ast.parse(expression, mode='eval')
            
            # Evaluate the AST
            result = Calculator._evaluate_node(tree.body)
            logger.info(f"Calculated: {expression} = {result}")
            return result
        
        except (ValueError, TypeError, ZeroDivisionError) as e:
            logger.error(f"Error evaluating expression '{expression}': {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error evaluating expression '{expression}': {str(e)}")
            raise ValueError(f"Invalid expression: {str(e)}")


def calculate(expression: str) -> Union[int, float]:
    """Convenience function to evaluate an expression."""
    return Calculator.evaluate(expression)
