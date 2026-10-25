#!/usr/bin/env python3
"""
pf_reg.py - tiny registry + assembly tree used by build_step.py.

* Part(...)  : one STEP file holding one fabricated part or one bought-in envelope.
* Asm        : a tree of placed parts (leaves keep their part id), exported as a nested
               cq.Assembly so the STEP file carries the product structure and part names.
* REG        : global registry; build_step.py serialises it to _build_index.json, which
               verify_step.py reads (so the verification is done on the files on disk).
"""
import json
import os
import cadquery as cq

OUT = os.path.dirname(os.path.abspath(__file__))

CLR = {   # same colour convention as pf_common.scad
    "struct": (0.66, 0.68, 0.71), "steel": (0.48, 0.50, 0.54), "print": (0.80, 0.81, 0.83),
    "elec": (0.16, 0.56, 0.27), "sensor": (0.15, 0.42, 0.82), "move": (0.96, 0.55, 0.10),
    "hw": (0.30, 0.31, 0.34), "rubber": (0.12, 0.12, 0.13),
}


class Leaf:
    def __init__(self, part_id, shape, name=None, color="struct", qty=1):
        self.part_id, self.shape, self.name, self.color, self.qty = part_id, shape, name or part_id, color, qty

    def moved(self, fn):
        return Leaf(self.part_id, fn(self.shape), self.name, self.color, self.qty)

    def leaves(self):
        return [self]

    def to_cq(self):
        raise RuntimeError


class Asm:
    def __init__(self, name, children=None):
        self.name = name
        self.children = list(children or [])

    def add(self, child):
        self.children.append(child)
        return self

    def moved(self, fn):
        return Asm(self.name, [c.moved(fn) for c in self.children])

    def leaves(self):
        out = []
        for c in self.children:
            out += c.leaves()
        return out

    def to_cq(self):
        a = cq.Assembly(name=self.name)
        for c in self.children:
            if isinstance(c, Leaf):
                a.add(c.shape, name=c.name, color=cq.Color(*CLR.get(c.color, CLR["struct"])))
            else:
                a.add(c.to_cq(), name=c.name)
        return a


def T(t=(0, 0, 0), r=(0, 0, 0)):
    """Placement function == OpenSCAD  translate(t) rotate(r) child  (also works on Asm.moved)."""
    from pf_cq import place
    return lambda s: place(s, t, r)


def compose(*fns):
    """compose(f, g, h)(s) == f(g(h(s)))  -> OpenSCAD reading order: f is the OUTERMOST transform."""
    def run(s):
        for f in reversed(fns):
            s = f(s)
        return s
    return run


class Registry:
    def __init__(self):
        self.parts = {}        # id -> meta
        self.asms = {}         # id -> meta (+ children summary)
        self.order = []

    # ------------------------------------------------------------------ parts
    def part(self, pid, shape, *, domain, desc, kind, material=None, params=(), ref=None,
             color="struct", qty=1, notes="", file=None, sources=(), mat_key=None, ref_fn=128, ref_includes=()):
        """kind: 'fabricated' | 'bought_envelope'.  `ref` = OpenSCAD snippet that produces the same
        part in the SAME frame (used by verify_step.py to make the comparison STL), or None."""
        assert pid not in self.parts, pid
        file = file or f"{pid}.step"
        self.parts[pid] = dict(id=pid, shape=shape, domain=domain, desc=desc, kind=kind, material=material,
                               params=list(params), ref=ref, color=color, qty=qty, notes=notes, file=file,
                               sources=list(sources), mat_key=mat_key, ref_fn=ref_fn, ref_includes=list(ref_includes))
        self.order.append(("part", pid))
        return shape

    def assembly(self, aid, asm, *, domain, desc, params=(), ref=None, notes="", file=None, sources=(),
                 ref_note="", ref_fn=48):
        assert aid not in self.asms, aid
        file = file or f"{aid}.step"
        self.asms[aid] = dict(id=aid, asm=asm, domain=domain, desc=desc, params=list(params), ref=ref,
                              notes=notes, file=file, sources=list(sources), ref_note=ref_note, ref_fn=ref_fn)
        self.order.append(("asm", aid))
        return asm

    # ------------------------------------------------------------------ export
    def export_all(self, outdir=OUT):
        for kind, i in self.order:
            if kind == "part":
                m = self.parts[i]
                a = cq.Assembly(name=i + "_container")
                shp = m["shape"]
                a.add(shp, name=i, color=cq.Color(*CLR.get(m["color"], CLR["struct"])))
                a.export(os.path.join(outdir, m["file"]))
            else:
                m = self.asms[i]
                m["asm"].to_cq().export(os.path.join(outdir, m["file"]))

    def index(self):
        from collections import Counter
        idx = {"parts": [], "assemblies": []}
        for i, m in self.parts.items():
            idx["parts"].append({k: m[k] for k in ("id", "domain", "desc", "kind", "material", "params", "ref",
                                                   "qty", "notes", "file", "sources", "mat_key", "ref_fn", "ref_includes")})
        for i, m in self.asms.items():
            cnt = Counter(l.part_id for l in m["asm"].leaves())
            idx["assemblies"].append({**{k: m[k] for k in ("id", "domain", "desc", "params", "ref", "notes",
                                                           "file", "sources", "ref_note", "ref_fn")},
                                      "contents": dict(cnt)})
        return idx

    def write_index(self, path=None):
        path = path or os.path.join(OUT, "_build_index.json")
        with open(path, "w") as f:
            json.dump(self.index(), f, indent=1)


REG = Registry()
