from __future__ import annotations

import ast
import math
import re
from typing import Any


class ToolWorkerError(RuntimeError):
    pass


def _fmt(value: Any) -> str:
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


_ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)
_ALLOWED_UNARY = (ast.UAdd, ast.USub)
_ALLOWED_CALLS = {"sum": sum, "len": len, "range": range, "sorted": sorted, "set": set, "max": max, "min": min, "list": list, "bool": bool, "abs": abs}


def _validate_expr(node: ast.AST) -> None:
    if isinstance(node, ast.Expression):
        _validate_expr(node.body)
    elif isinstance(node, ast.Constant):
        if not isinstance(node.value, (int, float, str, bool, type(None))):
            raise ToolWorkerError("UNSAFE_CONSTANT")
    elif isinstance(node, ast.BinOp):
        if not isinstance(node.op, _ALLOWED_BINOPS):
            raise ToolWorkerError("UNSAFE_OPERATOR")
        _validate_expr(node.left); _validate_expr(node.right)
    elif isinstance(node, ast.UnaryOp):
        if not isinstance(node.op, _ALLOWED_UNARY):
            raise ToolWorkerError("UNSAFE_UNARY")
        _validate_expr(node.operand)
    elif isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        for elt in node.elts:
            _validate_expr(elt)
    elif isinstance(node, ast.Dict):
        for key in node.keys:
            if key is not None:
                _validate_expr(key)
        for value in node.values:
            _validate_expr(value)
    elif isinstance(node, ast.Name):
        if node.id not in _ALLOWED_CALLS:
            raise ToolWorkerError("UNSAFE_NAME")
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id not in _ALLOWED_CALLS:
                raise ToolWorkerError("UNSAFE_CALL")
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr not in {"get", "join"}:
                raise ToolWorkerError("UNSAFE_ATTRIBUTE")
            _validate_expr(node.func.value)
        else:
            raise ToolWorkerError("UNSAFE_CALL_TARGET")
        for arg in node.args:
            _validate_expr(arg)
        for kw in node.keywords:
            _validate_expr(kw.value)
    elif isinstance(node, ast.Attribute):
        if node.attr not in {"get", "join"}:
            raise ToolWorkerError("UNSAFE_ATTRIBUTE")
        _validate_expr(node.value)
    elif isinstance(node, ast.Subscript):
        _validate_expr(node.value)
        _validate_expr(node.slice)
    elif isinstance(node, ast.Slice):
        for value in (node.lower, node.upper, node.step):
            if value is not None:
                _validate_expr(value)
    else:
        raise ToolWorkerError(f"UNSAFE_AST:{type(node).__name__}")


def safe_eval(expression: str):
    expression = expression.strip().replace("^", "**")
    if not expression or len(expression) > 220:
        raise ToolWorkerError("EXPRESSION_SIZE")
    tree = ast.parse(expression, mode="eval")
    _validate_expr(tree)
    return eval(compile(tree, "<cerebron-safe-eval>", "eval"), {"__builtins__": {}}, dict(_ALLOWED_CALLS))


def _numbers(text: str) -> list[float]:
    return [float(x) for x in re.findall(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)", text)]


def solve_math(prompt: str) -> dict | None:
    p = prompt.strip()
    m = re.search(r"Compute\s*:\s*([^\n.]+)", p, re.I)
    if m:
        return {"unit": "SM02", "method": "safe-arithmetic", "answer": _fmt(safe_eval(m.group(1)))}

    m = re.search(r"Solve for x\s*:\s*([-+]?\d+(?:\.\d+)?)\s*\*?x\s*([+-]\s*\d+(?:\.\d+)?)\s*=\s*([-+]?\d+(?:\.\d+)?)", p, re.I)
    if m:
        a = float(m.group(1)); b = float(m.group(2).replace(" ", "")); c = float(m.group(3))
        if a == 0:
            raise ToolWorkerError("ZERO_LINEAR_COEFFICIENT")
        return {"unit": "SM02", "method": "linear-equation", "answer": _fmt((c-b)/a)}

    m = re.search(r"gcd\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)", p, re.I)
    if m:
        return {"unit": "SM02", "method": "gcd", "answer": str(math.gcd(int(m.group(1)), int(m.group(2))))}

    m = re.search(r"([-+]?\d+(?:\.\d+)?)\s*percent of\s*([-+]?\d+(?:\.\d+)?)", p, re.I)
    if m:
        return {"unit": "SM02", "method": "percent", "answer": _fmt(float(m.group(1))*float(m.group(2))/100)}

    m = re.search(r"Convert\s+(\d+)\s*/\s*(\d+)\s+to decimal", p, re.I)
    if m:
        return {"unit": "SM02", "method": "fraction", "answer": _fmt(int(m.group(1))/int(m.group(2)))}

    m = re.search(r"triangle.*angles?\s+([-+]?\d+(?:\.\d+)?)\s+and\s+([-+]?\d+(?:\.\d+)?)", p, re.I)
    if m:
        return {"unit": "SM02", "method": "triangle-angle", "answer": _fmt(180-float(m.group(1))-float(m.group(2)))}

    m = re.search(r"mean of\s+([0-9.,\s+-]+)", p, re.I)
    if m:
        vals = _numbers(m.group(1))
        if vals:
            return {"unit": "SM02", "method": "mean", "answer": _fmt(sum(vals)/len(vals))}

    m = re.search(r"next number\s*:\s*([0-9.,\s+-]+)", p, re.I)
    if m:
        vals = _numbers(m.group(1))
        if len(vals) >= 4:
            d1 = [vals[i+1]-vals[i] for i in range(len(vals)-1)]
            d2 = [d1[i+1]-d1[i] for i in range(len(d1)-1)]
            if max(d2)-min(d2) < 1e-9:
                return {"unit": "SM02", "method": "finite-difference-sequence", "answer": _fmt(vals[-1] + d1[-1] + d2[-1])}
            if max(d1)-min(d1) < 1e-9:
                return {"unit": "SM02", "method": "arithmetic-sequence", "answer": _fmt(vals[-1] + d1[-1])}
    return None


def solve_code(prompt: str) -> dict | None:
    m = re.search(r"Python result\s*:\s*(.+)", prompt, re.I)
    if not m:
        return None
    expr = m.group(1).strip()
    if expr.endswith("."):
        expr = expr[:-1]
    value = safe_eval(expr)
    if isinstance(value, (list, tuple)):
        answer = ",".join(_fmt(v) for v in value)
    else:
        answer = _fmt(value)
    return {"unit": "SM05", "method": "restricted-python-expression", "answer": answer}


def _named_values(prompt: str) -> dict[str, float]:
    values = {}
    for key, value in re.findall(r"\b([A-Za-z][A-Za-z0-9_]*)\s*=\s*([-+]?\d+(?:\.\d+)?)", prompt):
        values[key.lower()] = float(value)
    return values


def solve_engineering(prompt: str) -> dict | None:
    p = prompt.lower()
    v = _named_values(prompt)
    try:
        if "f=ma" in p:
            ans = v["m"] * v["a"]
        elif "p=fv" in p:
            ans = v["f"] * v["v"]
        elif "e=pt" in p:
            ans = v["p"] * v["t"]
        elif "rho=m/v" in p:
            ans = v["m"] / v["v"]
        elif "v=d/t" in p:
            ans = v["d"] / v["t"]
        elif "v=ir" in p:
            ans = v["i"] * v["r"]
        elif "ke=0.5*m*v^2" in p:
            ans = 0.5 * v["m"] * v["v"] ** 2
        elif "pe=mgh" in p:
            ans = v["m"] * v["g"] * v["h"]
        elif "f=1/t" in p:
            ans = 1.0 / v["t"]
        elif "eta=100*pout/pin" in p:
            ans = 100.0 * v["pout"] / v["pin"]
        else:
            return None
    except (KeyError, ZeroDivisionError):
        return None
    return {"unit": "SM08", "method": "engineering-formula", "answer": _fmt(ans)}


def solve_research(prompt: str) -> dict | None:
    if "SOURCE:" not in prompt or "Using only the source" not in prompt:
        return None
    source = prompt.split("SOURCE:", 1)[1].split("Using only the source", 1)[0]
    pairs = {}
    for field in source.split(";"):
        if "=" not in field:
            continue
        key, value = field.split("=", 1)
        key = key.strip()
        value = value.strip().strip(".")
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", key):
            pairs[key.lower()] = value
    m = re.search(r"return only\s+([A-Za-z][A-Za-z0-9_-]*)", prompt, re.I)
    if m and m.group(1).lower() in pairs:
        return {"unit": "SM11", "method": "source-key-extraction", "answer": pairs[m.group(1).lower()]}
    return None


def solve_planning(prompt: str) -> dict | None:
    if "Constraints:" not in prompt or "Options:" not in prompt:
        return None
    constraint_text = prompt.split("Constraints:", 1)[1].split("Options:", 1)[0]
    option_text = prompt.split("Options:", 1)[1]
    constraints = [x.strip().rstrip(".") for x in constraint_text.split(";") if x.strip()]
    options = {}
    for label, seq in re.findall(r"\b([ABC])\s*=\s*([^;.]+)", option_text):
        options[label.lower()] = [x.strip() for x in seq.split(",") if x.strip()]

    def ok(seq: list[str]) -> bool:
        pos = {item: i for i, item in enumerate(seq)}
        for raw in constraints:
            c = raw.strip()
            m = re.fullmatch(r"(.+?)\s+before\s+(.+)", c, re.I)
            if m:
                a,b = m.group(1).strip(),m.group(2).strip()
                if a not in pos or b not in pos or pos[a] >= pos[b]: return False
                continue
            m = re.fullmatch(r"(.+?)\s+after\s+(.+)", c, re.I)
            if m:
                a,b = m.group(1).strip(),m.group(2).strip()
                if a not in pos or b not in pos or pos[a] <= pos[b]: return False
                continue
            m = re.fullmatch(r"(.+?)\s+immediately after\s+(.+)", c, re.I)
            if m:
                a,b = m.group(1).strip(),m.group(2).strip()
                if a not in pos or b not in pos or pos[a] != pos[b]+1: return False
                continue
            m = re.fullmatch(r"(.+?)\s+not first", c, re.I)
            if m:
                item = m.group(1).strip()
                if item not in pos or pos[item] == 0: return False
                continue
            m = re.fullmatch(r"(.+?)\s+first", c, re.I)
            if m:
                item = m.group(1).strip()
                if item not in pos or pos[item] != 0: return False
                continue
            m = re.fullmatch(r"(.+?)\s+last", c, re.I)
            if m:
                item = m.group(1).strip()
                if item not in pos or pos[item] != len(seq)-1: return False
                continue
        return True

    valid = [label for label, seq in options.items() if ok(seq)]
    if len(valid) == 1:
        return {"unit": "SM00", "method": "constraint-plan-checker", "answer": valid[0].upper()}
    return None


def solve_error_detection(prompt: str) -> dict | None:
    if "false" not in prompt.lower():
        return None
    claims = re.findall(r"\b([ABC])\s*:\s*([^;]+)", prompt)
    false_labels = []
    for label, claim in claims:
        m = re.fullmatch(r"\s*([-+0-9*/(). ^]+)\s*=\s*([-+]?\d+(?:\.\d+)?)\s*", claim.strip())
        if not m:
            return None
        left = float(safe_eval(m.group(1)))
        right = float(m.group(2))
        if abs(left-right) > 1e-9:
            false_labels.append(label)
    if len(false_labels) == 1:
        return {"unit": "SM15", "method": "arithmetic-claim-checker", "answer": false_labels[0]}
    return None


def try_solve(prompt: str) -> dict:
    for fn in (solve_research, solve_planning, solve_error_detection, solve_code, solve_engineering, solve_math):
        try:
            result = fn(prompt)
        except (ToolWorkerError, ValueError, SyntaxError, TypeError):
            result = None
        if result is not None:
            return {"handled": True, "status": "EXECUTED", **result}
    return {"handled": False, "status": "NOT_APPLICABLE"}
