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



# Semantic-contract routing V2.
# These wrappers preserve the bounded legacy solvers while accepting surface-form variation.
_solve_math_legacy = solve_math
_solve_code_legacy = solve_code
_solve_engineering_legacy = solve_engineering
_solve_research_legacy = solve_research
_solve_planning_legacy = solve_planning
_solve_error_legacy = solve_error_detection


def solve_math(prompt: str) -> dict | None:
    legacy = _solve_math_legacy(prompt)
    if legacy is not None:
        return legacy
    p = prompt.strip()

    m = re.search(r"(?:multiply|product of)\s+([-+]?\d+(?:\.\d+)?)\s+(?:by|and)\s+([-+]?\d+(?:\.\d+)?)", p, re.I)
    if m:
        return {"unit":"SM02","method":"semantic-product","answer":_fmt(float(m.group(1))*float(m.group(2)))}

    m = re.search(r"([-+]?\d+(?:\.\d+)?)\s+(?:divided by|over)\s+([-+]?\d+(?:\.\d+)?).*?(?:then\s+)?add\s+([-+]?\d+(?:\.\d+)?)", p, re.I)
    if m and float(m.group(2)) != 0:
        return {"unit":"SM02","method":"semantic-divide-add","answer":_fmt(float(m.group(1))/float(m.group(2))+float(m.group(3)))}

    m = re.search(r"(?:satisfies|equation)\s+([-+]?\d+(?:\.\d+)?)\s*\*?\s*x\s*([+-]\s*\d+(?:\.\d+)?)\s*=\s*([-+]?\d+(?:\.\d+)?)", p, re.I)
    if not m:
        m = re.search(r"([-+]?\d+(?:\.\d+)?)\s*\*?\s*x\s*([+-]\s*\d+(?:\.\d+)?)\s*=\s*([-+]?\d+(?:\.\d+)?)", p, re.I)
    if m:
        a=float(m.group(1)); b=float(m.group(2).replace(" ","")); c=float(m.group(3))
        if a != 0:
            return {"unit":"SM02","method":"semantic-linear-equation","answer":_fmt((c-b)/a)}

    m = re.search(r"greatest common divisor of\s+(\d+)\s+(?:and|,)\s*(\d+)", p, re.I)
    if m:
        return {"unit":"SM02","method":"semantic-gcd","answer":str(math.gcd(int(m.group(1)),int(m.group(2))))}

    m = re.search(r"([-+]?\d+(?:\.\d+)?)\s*%\s*(?:of)?\s*([-+]?\d+(?:\.\d+)?)", p, re.I)
    if m:
        return {"unit":"SM02","method":"semantic-percent","answer":_fmt(float(m.group(1))*float(m.group(2))/100.0)}

    m = re.search(r"(\d+)\s*/\s*(\d+).*?(?:decimal|decimal form)", p, re.I)
    if m and int(m.group(2)) != 0:
        return {"unit":"SM02","method":"semantic-fraction","answer":_fmt(int(m.group(1))/int(m.group(2)))}

    if "triangle" in p.lower():
        vals=[float(x) for x in re.findall(r"([-+]?\d+(?:\.\d+)?)\s*(?:°|degrees?)", p, re.I)]
        if len(vals) >= 2:
            return {"unit":"SM02","method":"semantic-triangle-angle","answer":_fmt(180.0-vals[0]-vals[1])}

    m = re.search(r"(?:arithmetic\s+average|average|mean)\s+(?:of\s+)?(?:these\s+\w+\s+values\s*:\s*)?([0-9.,\s+-]+)", p, re.I)
    if m:
        vals=_numbers(m.group(1))
        if vals:
            return {"unit":"SM02","method":"semantic-mean","answer":_fmt(sum(vals)/len(vals))}

    if re.search(r"(?:pattern|sequence|next term)", p, re.I):
        vals=_numbers(p)
        if len(vals) >= 4:
            d=[vals[i+1]-vals[i] for i in range(len(vals)-1)]
            if max(d)-min(d) < 1e-9:
                return {"unit":"SM02","method":"semantic-arithmetic-sequence","answer":_fmt(vals[-1]+d[-1])}

    m = re.search(r"([-+]?\d+(?:\.\d+)?)\s+(?:raised to the power|to the power)\s+([-+]?\d+(?:\.\d+)?)", p, re.I)
    if m:
        return {"unit":"SM02","method":"semantic-power","answer":_fmt(float(m.group(1))**float(m.group(2)))}
    return None


def solve_code(prompt: str) -> dict | None:
    legacy = _solve_code_legacy(prompt)
    if legacy is not None:
        return legacy
    m = re.search(
        r"(?:safe\s+python\s+expression|python\s+expression|restricted\s+(?:python\s+)?evaluator)\s*:\s*(.+?)(?:\.\s*(?:respond|reply|return)\b|$)",
        prompt, re.I,
    )
    if not m:
        return None
    expr=m.group(1).strip()
    value=safe_eval(expr)
    answer=",".join(_fmt(v) for v in value) if isinstance(value,(list,tuple)) else _fmt(value)
    return {"unit":"SM05","method":"semantic-restricted-python-expression","answer":answer}


def solve_engineering(prompt: str) -> dict | None:
    legacy = _solve_engineering_legacy(prompt)
    if legacy is not None:
        return legacy
    p=prompt.lower()
    patterns=[
        (r"(?:mass of\s+)?([-+]?\d+(?:\.\d+)?)\s*kg.*?accelerat(?:es|ion).*?([-+]?\d+(?:\.\d+)?)\s*m/s(?:\^?2|²)", lambda a,b:a*b, "force"),
        (r"force of\s+([-+]?\d+(?:\.\d+)?)\s*n.*?(?:moving at|motion at|speed(?: of)?)[^0-9+-]*([-+]?\d+(?:\.\d+)?)\s*m/s", lambda a,b:a*b, "power"),
        (r"(?:draws|uses)\s+([-+]?\d+(?:\.\d+)?)\s*w.*?for\s+([-+]?\d+(?:\.\d+)?)\s*(?:s|seconds?)", lambda a,b:a*b, "energy"),
        (r"mass(?: is| of)?\s*([-+]?\d+(?:\.\d+)?)\s*kg.*?volume(?: is| of)?\s*([-+]?\d+(?:\.\d+)?)\s*m(?:\^?3|³)", lambda a,b:a/b, "density"),
        (r"(?:travel|distance(?: is| of)?)\s*([-+]?\d+(?:\.\d+)?)\s*m.*?(?:in|time(?: is| of)?)\s*([-+]?\d+(?:\.\d+)?)\s*s", lambda a,b:a/b, "speed"),
        (r"current(?: is| of)?\s*([-+]?\d+(?:\.\d+)?)\s*a.*?([-+]?\d+(?:\.\d+)?)\s*ohm", lambda a,b:a*b, "voltage"),
        (r"(?:mass of\s+)?([-+]?\d+(?:\.\d+)?)\s*kg.*?moves? at\s*([-+]?\d+(?:\.\d+)?)\s*m/s.*?kinetic", lambda a,b:0.5*a*b*b, "kinetic-energy"),
        (r"(?:mass of\s+)?([-+]?\d+(?:\.\d+)?)\s*kg.*?lifted\s+([-+]?\d+(?:\.\d+)?)\s*m.*?gravity\s*([-+]?\d+(?:\.\d+)?)", lambda a,b,c:a*b*c, "potential-energy"),
        (r"(?:repeats every|period(?: is| of)?)\s*([-+]?\d+(?:\.\d+)?)\s*(?:s|seconds?)", lambda a:1.0/a, "frequency"),
        (r"input power(?: is| of)?\s*([-+]?\d+(?:\.\d+)?)\s*w.*?(?:useful\s+)?output(?: power)?(?: is| of)?\s*([-+]?\d+(?:\.\d+)?)\s*w", lambda a,b:100.0*b/a, "efficiency"),
    ]
    for regex,fn,name in patterns:
        m=re.search(regex,p,re.I)
        if m:
            vals=[float(x) for x in m.groups()]
            if any(v==0 for v in vals[1:]) and name in {"density","speed"}:
                return None
            return {"unit":"SM08","method":"semantic-engineering-"+name,"answer":_fmt(fn(*vals))}
    return None


def solve_research(prompt: str) -> dict | None:
    legacy = _solve_research_legacy(prompt)
    if legacy is not None:
        return legacy
    pairs={}
    for key,value in re.findall(r"\b([A-Za-z][A-Za-z0-9_-]*)\s*[:=]\s*([-+]?\d+(?:\.\d+)?|[A-Za-z][A-Za-z0-9_.-]*)",prompt):
        pairs[key.lower()]=value
    m=re.search(r"(?:value\s+(?:for|of)|provide\s+the\s+value\s+for|return only)\s+([A-Za-z][A-Za-z0-9_-]*)",prompt,re.I)
    if m and m.group(1).lower() in pairs and re.search(r"(?:reference|data|source|based solely|strictly)",prompt,re.I):
        return {"unit":"SM11","method":"semantic-source-key-extraction","answer":pairs[m.group(1).lower()]}
    return None


def _planning_options(prompt: str) -> dict[str,list[str]]:
    options={}
    for label,seq in re.findall(r"\b([A-Z0-9])\s*[:=]\s*([A-Za-z0-9_-]+(?:\s*(?:>|,)\s*[A-Za-z0-9_-]+){1,8})",prompt):
        parts=[x.strip() for x in re.split(r"\s*(?:>|,)\s*",seq) if x.strip()]
        if len(parts)>=2:
            options[label.upper()]=parts
    return options


def solve_planning(prompt: str) -> dict | None:
    legacy = _solve_planning_legacy(prompt)
    if legacy is not None:
        return legacy
    options=_planning_options(prompt)
    if len(options)<2:
        return None
    rules=[]
    for m in re.finditer(r"\b([A-Za-z0-9_-]+)\s+(?:must\s+)?(?:be\s+)?first\b",prompt,re.I):
        rules.append(("first",m.group(1),None))
    for m in re.finditer(r"\b([A-Za-z0-9_-]+)\s+(?:must\s+)?(?:be\s+)?last\b",prompt,re.I):
        rules.append(("last",m.group(1),None))
    for m in re.finditer(r"\b([A-Za-z0-9_-]+)\s+(?:must\s+)?(?:come\s+|occur\s+)?before\s+([A-Za-z0-9_-]+)",prompt,re.I):
        rules.append(("before",m.group(1),m.group(2)))
    for m in re.finditer(r"\b([A-Za-z0-9_-]+)\s+(?:must\s+)?(?:come\s+|occur\s+)?after\s+([A-Za-z0-9_-]+)",prompt,re.I):
        rules.append(("after",m.group(1),m.group(2)))
    def ok(seq):
        pos={x:i for i,x in enumerate(seq)}
        for kind,a,b in rules:
            if a not in pos:return False
            if kind=="first" and pos[a]!=0:return False
            if kind=="last" and pos[a]!=len(seq)-1:return False
            if kind=="before" and (b not in pos or pos[a]>=pos[b]):return False
            if kind=="after" and (b not in pos or pos[a]<=pos[b]):return False
        return True
    valid=[label for label,seq in options.items() if ok(seq)]
    if len(valid)==1 and rules:
        return {"unit":"SM00","method":"semantic-constraint-plan-checker","answer":valid[0]}
    return None


def solve_error_detection(prompt: str) -> dict | None:
    legacy = _solve_error_legacy(prompt)
    if legacy is not None:
        return legacy
    if not re.search(r"\b(?:wrong|false|incorrect)\b",prompt,re.I):
        return None
    claims=re.findall(r"\b([A-Z0-9])\s*[:)]\s*([^;]+)",prompt)
    bad=[]
    for label,claim in claims:
        m=re.fullmatch(r"\s*([-+0-9*/(). ^]+)\s*=\s*([-+]?\d+(?:\.\d+)?)\s*\.?\s*",claim.strip())
        if not m:
            continue
        if abs(float(safe_eval(m.group(1)))-float(m.group(2)))>1e-9:
            bad.append(label.upper())
    if len(bad)==1:
        return {"unit":"SM15","method":"semantic-arithmetic-claim-checker","answer":bad[0]}
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
