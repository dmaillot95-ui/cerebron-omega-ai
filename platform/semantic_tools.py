from __future__ import annotations

import re

from specialist_tools import ToolWorkerError, safe_eval, try_solve as legacy_try_solve


def _fmt(value):
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, (list, tuple)):
        return ",".join(_fmt(v) for v in value)
    return str(value)


def _num(pattern: str, text: str):
    m = re.search(pattern, text, re.I)
    return float(m.group(1)) if m else None


def solve_math_semantic(prompt: str):
    p = prompt.strip()

    patterns = [
        r"(?:multiply|multiplying)\s+([-+]?\d+(?:\.\d+)?)\s+(?:by|and)\s+([-+]?\d+(?:\.\d+)?)",
        r"(?:product of)\s+([-+]?\d+(?:\.\d+)?)\s+(?:and|with)\s+([-+]?\d+(?:\.\d+)?)",
        r"([-+]?\d+(?:\.\d+)?)\s+(?:times|multiplied by)\s+([-+]?\d+(?:\.\d+)?)",
    ]
    for pat in patterns:
        m = re.search(pat, p, re.I)
        if m:
            return {"unit": "SM02", "method": "semantic-arithmetic-product", "answer": _fmt(float(m.group(1))*float(m.group(2)))}

    m = re.search(
        r"(?:find|solve(?:\s+for)?|determine)\s+x.*?([-+]?\d+(?:\.\d+)?)\s*\*?\s*x\s*([+-]\s*\d+(?:\.\d+)?)\s*=\s*([-+]?\d+(?:\.\d+)?)",
        p, re.I,
    )
    if m:
        a=float(m.group(1)); b=float(m.group(2).replace(" ","")); c=float(m.group(3))
        if a == 0:
            raise ToolWorkerError("ZERO_LINEAR_COEFFICIENT")
        return {"unit": "SM02", "method": "semantic-linear-equation", "answer": _fmt((c-b)/a)}

    m = re.search(r"(?:greatest common divisor|gcd)\s+(?:of\s+)?(\d+)\s+(?:and|,)\s*(\d+)", p, re.I)
    if m:
        import math
        return {"unit": "SM02", "method": "semantic-gcd", "answer": str(math.gcd(int(m.group(1)),int(m.group(2))))}

    m = re.search(r"([-+]?\d+(?:\.\d+)?)\s*(?:%|percent)\s+(?:of|from)\s+([-+]?\d+(?:\.\d+)?)", p, re.I)
    if m:
        return {"unit": "SM02", "method": "semantic-percent", "answer": _fmt(float(m.group(1))*float(m.group(2))/100.0)}
    return None


def _extract_expression(prompt: str):
    candidates = [
        r"(?:python\s+)?expression\s*[:=]\s*(.+)",
        r"(?:evaluate|compute)\s+(?:this\s+)?(?:python\s+)?expression\s*[:=]?\s*(.+)",
        r"(?:result|value)\s+of\s+(?:the\s+)?(?:python\s+)?expression\s*[:=]?\s*(.+)",
    ]
    for pat in candidates:
        m=re.search(pat,prompt,re.I)
        if m:
            expr=m.group(1).strip()
            expr=re.split(r"\b(?:reply|return|answer)\b",expr,flags=re.I)[0].strip()
            return expr.rstrip(" .")
    return None


def solve_code_semantic(prompt: str):
    if "python" not in prompt.lower() and "expression" not in prompt.lower():
        return None
    expr=_extract_expression(prompt)
    if not expr:
        return None
    value=safe_eval(expr)
    return {"unit":"SM05","method":"semantic-restricted-python-expression","answer":_fmt(value)}


def _assigned(prompt: str, name: str):
    m=re.search(rf"\b{re.escape(name)}\s*=\s*([-+]?\d+(?:\.\d+)?)",prompt,re.I)
    return float(m.group(1)) if m else None


def _unit_value(prompt: str, word_pat: str, unit_pat: str):
    patterns=[
        rf"(?:{word_pat})[^\d+-]*([-+]?\d+(?:\.\d+)?)\s*(?:{unit_pat})",
        rf"([-+]?\d+(?:\.\d+)?)\s*(?:{unit_pat})[^.\n;]*(?:{word_pat})",
    ]
    for pat in patterns:
        m=re.search(pat,prompt,re.I)
        if m:
            return float(m.group(1))
    return None


def solve_engineering_semantic(prompt: str):
    p=prompt.lower()
    compact=re.sub(r"\s+","",p)

    m=_assigned(prompt,"m") or _unit_value(prompt,r"mass","kg")
    a=_assigned(prompt,"a") or _unit_value(prompt,r"acceleration|accelerates?\s+at","m/s\^?2|m/s2")
    f=_assigned(prompt,"f") or _unit_value(prompt,r"force","n|newtons?")
    v=_assigned(prompt,"v") or _unit_value(prompt,r"speed|velocity|motion\s+at","m/s")
    t=_assigned(prompt,"t") or _unit_value(prompt,r"time|duration|period","s|seconds?")
    power=_assigned(prompt,"p") or _unit_value(prompt,r"power","w|watts?")
    current=_assigned(prompt,"i") or _unit_value(prompt,r"current","a|amps?|amperes?")
    resistance=_assigned(prompt,"r") or _unit_value(prompt,r"resistance","ohm|ohms")
    voltage=_assigned(prompt,"v") or _unit_value(prompt,r"voltage","v|volts?")
    height=_assigned(prompt,"h") or _unit_value(prompt,r"height","m|meters?")
    g=_assigned(prompt,"g")

    if ("f=m*a" in compact or "f=ma" in compact or ("force" in p and "mass" in p and "accelerat" in p)) and m is not None and a is not None:
        return {"unit":"SM08","method":"semantic-engineering-formula:F=ma","answer":_fmt(m*a)}
    if ("p=f*v" in compact or "p=fv" in compact or ("power" in p and "force" in p and ("speed" in p or "velocity" in p))) and f is not None and v is not None:
        return {"unit":"SM08","method":"semantic-engineering-formula:P=Fv","answer":_fmt(f*v)}
    if ("e=p*t" in compact or "e=pt" in compact or ("energy" in p and "power" in p and ("duration" in p or "time" in p))) and power is not None and t is not None:
        return {"unit":"SM08","method":"semantic-engineering-formula:E=Pt","answer":_fmt(power*t)}
    if ("v=i*r" in compact or "v=ir" in compact or ("voltage" in p and "current" in p and "resistance" in p)) and current is not None and resistance is not None:
        return {"unit":"SM08","method":"semantic-engineering-formula:V=IR","answer":_fmt(current*resistance)}
    if ("kinetic energy" in p or "ke=" in compact) and m is not None and v is not None:
        return {"unit":"SM08","method":"semantic-engineering-formula:KE","answer":_fmt(0.5*m*v*v)}
    if ("potential energy" in p or "mgh" in compact) and m is not None and g is not None and height is not None:
        return {"unit":"SM08","method":"semantic-engineering-formula:PE","answer":_fmt(m*g*height)}
    if ("frequency" in p or "f=1/t" in compact) and t is not None and t != 0:
        return {"unit":"SM08","method":"semantic-engineering-formula:f=1/T","answer":_fmt(1.0/t)}
    return None


def _source_block(prompt: str):
    m=re.search(r"\b(?:source|data|facts|context)\s*:\s*(.+)",prompt,re.I|re.S)
    if not m:
        return None
    block=m.group(1)
    block=re.split(r"\b(?:using only|based strictly|based only|according to|from this|answer|return|what is|give)\b",block,flags=re.I)[0]
    return block.strip()


def _parse_source_pairs(block: str):
    pairs={}
    for seg in re.split(r"[;\n]+",block):
        seg=seg.strip(" .")
        if not seg:
            continue
        m=re.match(r"([A-Za-z][A-Za-z0-9_-]*)\s*(?:=|:|\bis\b)\s*([^;]+)",seg,re.I)
        if m:
            pairs[m.group(1).lower()]=m.group(2).strip(" .")
    return pairs


def solve_research_semantic(prompt: str):
    block=_source_block(prompt)
    if not block:
        return None
    pairs=_parse_source_pairs(block)
    if not pairs:
        return None

    target=None
    patterns=[
        r"(?:value|field|entry)\s+(?:of|for)\s+([A-Za-z][A-Za-z0-9_-]*)",
        r"(?:return|answer|give)\s+(?:only\s+)?(?:the\s+)?(?:value\s+(?:of|for)\s+)?([A-Za-z][A-Za-z0-9_-]*)",
        r"what\s+is\s+([A-Za-z][A-Za-z0-9_-]*)",
    ]
    for pat in patterns:
        m=re.search(pat,prompt,re.I)
        if m and m.group(1).lower() in pairs:
            target=m.group(1).lower(); break
    if target:
        return {"unit":"SM11","method":"semantic-grounded-field-extraction","answer":pairs[target]}
    return None


def _option_sequences(prompt: str):
    matches=list(re.finditer(r"\b([ABC])\s*[:=]\s*",prompt,re.I))
    opts={}
    for i,m in enumerate(matches):
        start=m.end()
        end=matches[i+1].start() if i+1<len(matches) else len(prompt)
        chunk=prompt[start:end]
        chunk=re.split(r"[.;]\s*(?:constraints?|choose|reply|answer)\b",chunk,flags=re.I)[0]
        items=[x.strip(" .") for x in re.split(r"\s*(?:>|→|,|/)\s*",chunk) if x.strip(" .")]
        if 2 <= len(items) <= 8:
            opts[m.group(1).lower()]=items
    return opts


def solve_planning_semantic(prompt: str):
    low=prompt.lower()
    if not any(x in low for x in ("option","candidate","order","schedule","sequence")):
        return None
    opts=_option_sequences(prompt)
    if len(opts)<2:
        return None

    clauses=[x.strip() for x in re.split(r"[;,.]",prompt) if x.strip()]
    rules=[]
    for c in clauses:
        patterns=[
            ("before",r"\b([A-Za-z][A-Za-z0-9_-]*)\b.*?\b(?:must\s+)?(?:occur\s+|come\s+)?before\s+\b([A-Za-z][A-Za-z0-9_-]*)\b"),
            ("after",r"\b([A-Za-z][A-Za-z0-9_-]*)\b.*?\b(?:must\s+)?(?:occur\s+|come\s+)?after\s+\b([A-Za-z][A-Za-z0-9_-]*)\b"),
            ("before",r"\b([A-Za-z][A-Za-z0-9_-]*)\b\s+(?:must\s+)?precede\s+\b([A-Za-z][A-Za-z0-9_-]*)\b"),
            ("first",r"\b([A-Za-z][A-Za-z0-9_-]*)\b\s+(?:must\s+be|is)\s+first\b"),
            ("last",r"\b([A-Za-z][A-Za-z0-9_-]*)\b\s+(?:must\s+be|is)\s+last\b"),
            ("not_first",r"\b([A-Za-z][A-Za-z0-9_-]*)\b\s+(?:must\s+)?not\s+(?:be\s+)?first\b"),
        ]
        for kind,pat in patterns:
            m=re.search(pat,c,re.I)
            if m:
                rules.append((kind,)+tuple(x.strip() for x in m.groups())); break

    if not rules:
        return None

    def ok(seq):
        pos={x:i for i,x in enumerate(seq)}
        for rule in rules:
            kind=rule[0]
            if kind in ("before","after"):
                a,b=rule[1],rule[2]
                if a not in pos or b not in pos: return False
                if kind=="before" and not (pos[a] < pos[b]): return False
                if kind=="after" and not (pos[a] > pos[b]): return False
            elif kind=="first":
                a=rule[1]
                if a not in pos or pos[a] != 0: return False
            elif kind=="last":
                a=rule[1]
                if a not in pos or pos[a] != len(seq)-1: return False
            elif kind=="not_first":
                a=rule[1]
                if a not in pos or pos[a] == 0: return False
        return True

    valid=[label for label,seq in opts.items() if ok(seq)]
    if len(valid)==1:
        return {"unit":"SM00","method":"semantic-constraint-plan-checker","answer":valid[0].upper()}
    return None


def _claims(prompt: str):
    matches=list(re.finditer(r"\b([ABC])\s*[:.)]\s*",prompt,re.I))
    out=[]
    for i,m in enumerate(matches):
        start=m.end(); end=matches[i+1].start() if i+1<len(matches) else len(prompt)
        chunk=prompt[start:end].strip(" ;.")
        out.append((m.group(1).upper(),chunk))
    return out


def solve_error_semantic(prompt: str):
    if not any(word in prompt.lower() for word in ("false","wrong","incorrect","invalid")):
        return None
    parsed=[]
    for label,claim in _claims(prompt):
        m=re.fullmatch(r"\s*([-+0-9*/(). ^]+)\s*=\s*([-+]?\d+(?:\.\d+)?)\s*",claim)
        if not m:
            return None
        left=float(safe_eval(m.group(1)))
        right=float(m.group(2))
        parsed.append((label,abs(left-right)>1e-9))
    wrong=[label for label,is_wrong in parsed if is_wrong]
    if len(wrong)==1:
        return {"unit":"SM15","method":"semantic-arithmetic-claim-checker","answer":wrong[0]}
    return None


def semantic_try_solve(prompt: str):
    legacy=legacy_try_solve(prompt)
    if legacy.get("handled"):
        return legacy
    for fn in (
        solve_research_semantic,
        solve_planning_semantic,
        solve_error_semantic,
        solve_code_semantic,
        solve_engineering_semantic,
        solve_math_semantic,
    ):
        try:
            result=fn(prompt)
        except (ToolWorkerError, ValueError, SyntaxError, TypeError, ZeroDivisionError):
            result=None
        if result is not None:
            return {"handled":True,"status":"EXECUTED","semantic_dispatch":True,**result}
    return {"handled":False,"status":"NOT_APPLICABLE","semantic_dispatch":True}
