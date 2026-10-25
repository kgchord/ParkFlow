#!/usr/bin/env python3
"""Post-processing helpers: distances to singular features, region filters, tables."""
import numpy as np


def dist_segments(P, segs):
    """P (n,3); segs list of (a,b) 3-vectors. returns min distance (n,)"""
    P = np.asarray(P, float)
    dmin = np.full(len(P), np.inf)
    for a, b in segs:
        a = np.asarray(a, float); b = np.asarray(b, float)
        ab = b - a
        t = np.clip(((P - a) @ ab) / (ab @ ab), 0.0, 1.0)
        q = a + t[:, None] * ab
        dmin = np.minimum(dmin, np.linalg.norm(P - q, axis=1))
    return dmin


def dist_circles(P, circles):
    """circles: list of (centre(3), radius, axis unit(3))"""
    P = np.asarray(P, float)
    dmin = np.full(len(P), np.inf)
    for c, r, ax in circles:
        c = np.asarray(c, float); ax = np.asarray(ax, float)
        v = P - c
        h = v @ ax
        rho = np.linalg.norm(v - h[:, None] * ax, axis=1)
        dmin = np.minimum(dmin, np.hypot(rho - r, h))
    return dmin


def top_k(vals, mask, k=1):
    v = np.where(mask, vals, -np.inf)
    idx = np.argsort(v)[::-1][:k]
    return idx
