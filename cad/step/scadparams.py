#!/usr/bin/env python3
"""
scadparams.py - read named numeric parameters out of the OpenSCAD source files so that
the STEP builders and the .scad models share ONE source of truth.

Only top-level, side-effect-free assignments of the form   name = <expression>;
are read (anything inside module/function bodies, and any name containing '$', is ignored).
Expressions are evaluated with a tiny, whitelisted evaluator (numbers, + - * / **, parentheses,
lists, PI, and the math functions sin/cos/tan/sqrt/abs/min/max/round/floor/ceil with OpenSCAD
degree semantics for the trig functions).  Anything that cannot be evaluated (strings, calls to
user modules, ...) is skipped and listed in `Params.skipped`.

Usage
-----
    from scadparams import load
    P = load("gantry_params.scad", "gantry_antenna_bracket.scad", "pf_bought.scad")
    P.bp_t   # 16.0
    P["bp_t"]
Unknown names raise KeyError / AttributeError, so a typo or a renamed variable in the .scad
file fails the build loudly instead of silently using a stale number.
"""
import math
import os
import re

SCAD_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "openscad"))

_FUNCS = {
    "sin": lambda a: math.sin(math.radians(a)),
    "cos": lambda a: math.cos(math.radians(a)),
    "tan": lambda a: math.tan(math.radians(a)),
    "sqrt": math.sqrt, "abs": abs, "min": min, "max": max,
    "round": lambda v: int(math.floor(v + 0.5)), "floor": math.floor, "ceil": math.ceil,
    "len": len, "PI": math.pi,
}


def _strip_comments(src):
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return re.sub(r"//[^\n]*", "", src)


def _top_level_statements(src):
    """Yield ';'-terminated statements that sit at brace depth 0 and bracket depth 0."""
    depth = 0
    cur = []
    for ch in src:
        if ch == "{":
            depth += 1
            cur = []
            continue
        if ch == "}":
            depth -= 1
            cur = []
            continue
        if depth > 0:
            continue
        if ch == ";":
            yield "".join(cur).strip()
            cur = []
        else:
            cur.append(ch)


_ASSIGN = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", re.S)


class Params(dict):
    def __init__(self):
        super().__init__()
        self.skipped = []
        self.origin = {}          # name -> file it was read from
        self._loaded = set()

    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError:
            raise AttributeError(k)

    def used(self, *names):
        return {n: self[n] for n in names}


def _eval(expr, env):
    expr = expr.strip()
    if "$" in expr or '"' in expr or "[for" in expr.replace(" ", "") or "?" in expr:
        raise ValueError("unsupported")
    # OpenSCAD '^' is not power; '**' not used. Only allow safe characters.
    if re.search(r"[^0-9A-Za-z_\.\+\-\*/\(\)\[\]\s,:]", expr):
        raise ValueError("unsupported chars")
    if ":" in expr:
        raise ValueError("range")
    scope = dict(_FUNCS)
    scope.update(env)
    return eval(expr, {"__builtins__": {}}, scope)       # noqa: S307 (whitelisted, sanitized above)


def load(*files, into=None):
    """Load parameters from the given .scad files (relative to cad/openscad) in order.
    Later files override earlier ones (same as OpenSCAD include order)."""
    P = into if into is not None else Params()
    for f in files:
        P._loaded.add(os.path.basename(f))
        path = f if os.path.isabs(f) else os.path.join(SCAD_DIR, f)
        with open(path) as fh:
            src = _strip_comments(fh.read())
        # honour include<> (OpenSCAD copies the variables of included files); use<> is ignored
        for inc in re.findall(r"^\s*include\s*<([^>]+)>", src, flags=re.M):
            if inc not in P._loaded:
                P._loaded.add(inc)
                load(inc, into=P)
        src = re.sub(r"^\s*(include|use)\s*<[^>]+>", "", src, flags=re.M)
        pending = []
        for st in _top_level_statements(src):
            m = _ASSIGN.match(st)
            if not m:
                continue
            name, expr = m.group(1), m.group(2)
            if name.startswith("$"):
                continue
            pending.append((name, expr))
        # evaluate; a few passes to resolve forward references inside the same file
        for _ in range(4):
            left = []
            for name, expr in pending:
                try:
                    P[name] = float(_eval(expr, P)) if not _is_list(expr) else _eval(expr, P)
                    P.origin[name] = os.path.basename(path)
                except Exception:       # unresolved this pass
                    left.append((name, expr))
            if len(left) == len(pending):
                break
            pending = left
        for name, expr in pending:
            P.skipped.append((os.path.basename(path), name, expr.strip()[:60]))
    return P


def _is_list(expr):
    return expr.strip().startswith("[")


if __name__ == "__main__":
    import sys
    P = load(*sys.argv[1:])
    for k, v in P.items():
        print(f"{k:22s} = {v}   ({P.origin[k]})")
    if P.skipped:
        print("\nskipped:", *P.skipped, sep="\n  ")
