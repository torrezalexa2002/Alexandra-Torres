import ast
import math
import operator
from collections.abc import Callable


_BINARY_OPERATORS: dict[type[ast.operator], Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}
_UNARY_OPERATORS: dict[type[ast.unaryop], Callable[[float], float]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}
_FUNCTIONS: dict[str, Callable[[float], float]] = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "exp": math.exp,
    "log": math.log,
    "sqrt": math.sqrt,
    "abs": abs,
}
_CONSTANTS = {"pi": math.pi, "e": math.e}


def evaluate_expression(expression: str, x: float) -> float:
    if not expression.strip() or len(expression) > 200:
        raise ValueError("Escribe una función válida de hasta 200 caracteres.")

    try:
        tree = ast.parse(expression, mode="eval")
        value = _evaluate_node(tree.body, x)
    except (SyntaxError, TypeError, ValueError, ZeroDivisionError, OverflowError) as error:
        raise ValueError(
            "No se pudo evaluar la función. Revisa la expresión y su dominio."
        ) from error

    if not math.isfinite(value):
        raise ValueError("La función produjo un resultado no finito.")
    return value


def _evaluate_node(node: ast.AST, x: float) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)

    if isinstance(node, ast.Name):
        if node.id == "x":
            return x
        if node.id in _CONSTANTS:
            return _CONSTANTS[node.id]
        raise ValueError("Solo puedes usar x, pi y e como variables.")

    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        left = _evaluate_node(node.left, x)
        right = _evaluate_node(node.right, x)
        if isinstance(node.op, ast.Pow) and abs(right) > 1000:
            raise ValueError("El exponente no puede superar 1000.")
        return _BINARY_OPERATORS[type(node.op)](left, right)

    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        return _UNARY_OPERATORS[type(node.op)](_evaluate_node(node.operand, x))

    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in _FUNCTIONS
        and len(node.args) == 1
        and not node.keywords
    ):
        return _FUNCTIONS[node.func.id](_evaluate_node(node.args[0], x))

    raise ValueError("La expresión contiene una operación no permitida.")


def solve(method: str, expression: str, parameters: dict[str, int | float]) -> dict[str, float | int]:
    function = lambda value: evaluate_expression(expression, value)

    if method == "bisection":
        return _bisection(function, parameters)
    if method == "newton":
        return _newton(function, parameters)
    if method == "trapezoid":
        return _trapezoid(function, parameters)
    if method == "simpson":
        return _simpson(function, parameters)
    raise ValueError("El método numérico seleccionado no es válido.")


def _validated_bounds(parameters: dict[str, int | float]) -> tuple[float, float]:
    lower = float(parameters["a"])
    upper = float(parameters["b"])
    if not math.isfinite(lower) or not math.isfinite(upper) or lower >= upper:
        raise ValueError("El límite a debe ser menor que b; ambos deben ser finitos.")
    return lower, upper


def _validated_tolerance(parameters: dict[str, int | float]) -> float:
    tolerance = float(parameters["tolerance"])
    if not math.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("La tolerancia debe ser un número positivo y finito.")
    return tolerance


def _bisection(
    function: Callable[[float], float], parameters: dict[str, int | float]
) -> dict[str, float | int]:
    lower, upper = _validated_bounds(parameters)
    tolerance = _validated_tolerance(parameters)
    max_iterations = int(parameters["max_iterations"])
    if not 1 <= max_iterations <= 1000:
        raise ValueError("El máximo de iteraciones debe estar entre 1 y 1000.")

    lower_value = function(lower)
    upper_value = function(upper)
    if lower_value == 0:
        return {"value": lower, "iterations": 0, "residual": 0.0}
    if upper_value == 0:
        return {"value": upper, "iterations": 0, "residual": 0.0}
    if lower_value * upper_value > 0:
        raise ValueError("La función debe cambiar de signo entre a y b.")

    midpoint = (lower + upper) / 2
    residual = abs(function(midpoint))
    for iteration in range(1, max_iterations + 1):
        midpoint = (lower + upper) / 2
        midpoint_value = function(midpoint)
        residual = abs(midpoint_value)
        if residual <= tolerance or (upper - lower) / 2 <= tolerance:
            return {"value": midpoint, "iterations": iteration, "residual": residual}
        if lower_value * midpoint_value < 0:
            upper = midpoint
        else:
            lower = midpoint
            lower_value = midpoint_value

    return {"value": midpoint, "iterations": max_iterations, "residual": residual}


def _newton(
    function: Callable[[float], float], parameters: dict[str, int | float]
) -> dict[str, float | int]:
    current = float(parameters["x0"])
    tolerance = _validated_tolerance(parameters)
    max_iterations = int(parameters["max_iterations"])
    if not math.isfinite(current):
        raise ValueError("La aproximación inicial debe ser finita.")
    if not 1 <= max_iterations <= 1000:
        raise ValueError("El máximo de iteraciones debe estar entre 1 y 1000.")

    for iteration in range(max_iterations + 1):
        value = function(current)
        residual = abs(value)
        if residual <= tolerance:
            return {"value": current, "iterations": iteration, "residual": residual}
        if iteration == max_iterations:
            break

        step = math.sqrt(math.ulp(1.0)) * max(1.0, abs(current))
        derivative = (function(current + step) - function(current - step)) / (2 * step)
        if not math.isfinite(derivative) or abs(derivative) < 1e-14:
            raise ValueError("La derivada es cero o indefinida cerca de la aproximación.")
        current -= value / derivative
        if not math.isfinite(current):
            raise ValueError("El método diverge; prueba otra aproximación inicial.")

    return {"value": current, "iterations": max_iterations, "residual": abs(function(current))}


def _trapezoid(
    function: Callable[[float], float], parameters: dict[str, int | float]
) -> dict[str, float | int]:
    lower, upper = _validated_bounds(parameters)
    intervals = _validated_intervals(parameters["intervals"], minimum=1)
    step = (upper - lower) / intervals
    total = (function(lower) + function(upper)) / 2
    total += sum(function(lower + index * step) for index in range(1, intervals))
    return {"value": total * step, "intervals": intervals}


def _simpson(
    function: Callable[[float], float], parameters: dict[str, int | float]
) -> dict[str, float | int]:
    lower, upper = _validated_bounds(parameters)
    intervals = _validated_intervals(parameters["intervals"], minimum=2)
    if intervals % 2:
        raise ValueError("Simpson 1/3 requiere un número par de subintervalos.")

    step = (upper - lower) / intervals
    total = function(lower) + function(upper)
    total += 4 * sum(
        function(lower + index * step) for index in range(1, intervals, 2)
    )
    total += 2 * sum(
        function(lower + index * step) for index in range(2, intervals, 2)
    )
    return {"value": total * step / 3, "intervals": intervals}


def _validated_intervals(value: int | float, minimum: int) -> int:
    intervals = int(value)
    if intervals != value or not minimum <= intervals <= 100000:
        raise ValueError("El número de subintervalos debe estar entre 1 y 100000.")
    return intervals
