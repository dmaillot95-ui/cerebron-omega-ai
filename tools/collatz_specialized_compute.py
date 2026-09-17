#!/usr/bin/env python3
import argparse, json, math

try:
    import sympy as sp
except Exception:
    sp = None
try:
    from z3 import Int, Solver, sat
except Exception:
    Int = Solver = sat = None
try:
    import networkx as nx
except Exception:
    nx = None


def vp(n, p):
    if n <= 0:
        raise ValueError('vp expects a positive integer')
    v = 0
    while n % p == 0:
        n //= p
        v += 1
    return v


def admissible_state(u, r, h):
    if u < 1 or r < 1 or h < 5 or h % 6 != 5:
        return False
    return vp((4 ** r) * h + 1, 3) == u


def hcouples(a, b):
    uj, rj, hj = a
    un, rn, hn = b
    return (2 ** (un + 2 * rn)) * hn - (3 ** (un + rj)) * hj == (3 ** un) - (2 ** un)


def symbolic_identity(max_r=12):
    rows = []
    for r in range(1, max_r + 1):
        z0 = sp.symbols('z0', integer=True) if sp else None
        if sp:
            z = z0
            for _ in range(r):
                z = (3 * z + 2) / 4
            residual = sp.simplify(4 ** r * z - (3 ** r * z0 + 2 * (4 ** r - 3 ** r)))
            ok = residual == 0
        else:
            ok = None
        rows.append({'r': r, 'identity_verified': ok})
    if sp:
        un, rj, rn, hj, hn = sp.symbols('u_n r_j r_n h_j h_n', integer=True, positive=True)
        lhs_product = 3 ** un * (3 ** rj * hj + 1)
        rhs_product = 2 ** un * (4 ** rn * hn + 1)
        expanded_residual = sp.expand(lhs_product - rhs_product)
        target_residual = -(2 ** (un + 2 * rn) * hn - 3 ** (un + rj) * hj - (3 ** un - 2 ** un))
        coupling_form_equivalent = sp.simplify(expanded_residual - target_residual) == 0
    else:
        coupling_form_equivalent = None
    return {'worker': 'sympy', 'claim_level': 'FINITE_SYMBOLIC_VERIFICATION', 'rows': rows,
            'hcoupling_forms_equivalent': coupling_form_equivalent}


def modular_scan(umax=10, rmax=60, hmax=5000):
    hits = []
    admissible_count = 0
    for u in range(1, umax + 1):
        for r in range(1, rmax + 1):
            hs = [h for h in range(5, hmax + 1, 6) if admissible_state(u, r, h)]
            if hs:
                admissible_count += len(hs)
                hits.append({'u': u, 'r': r, 'h_min': hs[0], 'count_le_hmax': len(hs),
                             'r_mod_3u_minus_1': r % (3 ** (u - 1))})
    return {'worker': 'modular', 'claim_level': 'FINITE_ENUMERATION',
            'bounds': {'u': umax, 'r': rmax, 'h': hmax},
            'state_conditions': ['h>=5', 'h≡5 mod 6', 'v3(4^r h + 1)=u'],
            'admissible_state_count': admissible_count, 'hits': hits}


def z3_hcoupling(umax=8, rmax=10, hmax=3000, max_solutions=500):
    if Solver is None:
        return {'worker': 'z3', 'claim_level': 'UNAVAILABLE', 'error': 'z3-solver unavailable'}
    sols = []
    checked_parameter_cells = 0
    for uj in range(1, umax + 1):
        for un in range(1, umax + 1):
            for rj in range(1, rmax + 1):
                for rn in range(1, rmax + 1):
                    checked_parameter_cells += 1
                    hj = Int('hj'); hn = Int('hn')
                    s = Solver()
                    s.add(hj >= 5, hj <= hmax, hn >= 5, hn <= hmax)
                    s.add(hj % 6 == 5, hn % 6 == 5)
                    s.add(((4 ** rj) * hj + 1) % (3 ** uj) == 0)
                    s.add(((4 ** rj) * hj + 1) % (3 ** (uj + 1)) != 0)
                    s.add(((4 ** rn) * hn + 1) % (3 ** un) == 0)
                    s.add(((4 ** rn) * hn + 1) % (3 ** (un + 1)) != 0)
                    s.add((2 ** (un + 2 * rn)) * hn - (3 ** (un + rj)) * hj == 3 ** un - 2 ** un)
                    while len(sols) < max_solutions and s.check() == sat:
                        m = s.model(); hv = m[hj].as_long(); nv = m[hn].as_long()
                        sols.append({'u_j': uj, 'u_next': un, 'r_j': rj, 'r_next': rn,
                                     'h_j': hv, 'h_next': nv,
                                     'v2_transition': vp((3 ** rj) * hv + 1, 2)})
                        s.add((hj != hv) | (hn != nv))
                    if len(sols) >= max_solutions: break
                if len(sols) >= max_solutions: break
            if len(sols) >= max_solutions: break
        if len(sols) >= max_solutions: break
    return {'worker': 'z3', 'claim_level': 'BOUNDED_SAT_SEARCH',
            'bounds': {'u': umax, 'r': rmax, 'h': hmax, 'max_solutions': max_solutions},
            'state_conditions': ['h>=5', 'h≡5 mod 6', 'v3(4^r h + 1)=u', 'exact H-coupling'],
            'checked_parameter_cells': checked_parameter_cells,
            'solutions_count': len(sols), 'solutions': sols}


def rank_features(s):
    u, r, h = s
    return {
        'u': float(u),
        'r': float(r),
        'logh': math.log(h),
        'log3rh1': math.log((3 ** r) * h + 1),
        'log4rh1': math.log((4 ** r) * h + 1),
        'logx': math.log(2 * (3 ** r) * h + 1),
    }


def discover_ranks(edges):
    if not edges:
        return {'tested': 0, 'strict_candidates': []}
    base_names = ['u', 'r', 'logh', 'log3rh1', 'log4rh1', 'logx']
    simple = []
    for name in base_names:
        ds = [rank_features(b)[name] - rank_features(a)[name] for a, b in edges]
        simple.append({'formula': name, 'min_delta': min(ds), 'max_delta': max(ds),
                       'strict_increasing': min(ds) > 1e-12,
                       'strict_decreasing': max(ds) < -1e-12})
    strict = [x for x in simple if x['strict_increasing'] or x['strict_decreasing']]
    tested = len(simple)
    # Small integer linear combinations of (u,r,logh). This is discovery only.
    for au in range(-4, 5):
        for ar in range(-4, 5):
            for ah in range(-4, 5):
                if (au, ar, ah) == (0, 0, 0):
                    continue
                # normalize sign/scale duplicates by primitive gcd and first nonzero positive
                import math as _m
                g = _m.gcd(_m.gcd(abs(au), abs(ar)), abs(ah))
                if g > 1: continue
                first = next(x for x in (au, ar, ah) if x != 0)
                if first < 0: continue
                ds = []
                for a, b in edges:
                    fa, fb = rank_features(a), rank_features(b)
                    ds.append(au*(fb['u']-fa['u']) + ar*(fb['r']-fa['r']) + ah*(fb['logh']-fa['logh']))
                tested += 1
                mn, mx = min(ds), max(ds)
                if mn > 1e-12 or mx < -1e-12:
                    strict.append({'formula': f'{au}*u + {ar}*r + {ah}*logh',
                                   'coeffs': [au, ar, ah], 'min_delta': mn, 'max_delta': mx,
                                   'strict_increasing': mn > 1e-12,
                                   'strict_decreasing': mx < -1e-12})
    strict.sort(key=lambda x: min(abs(x['min_delta']), abs(x['max_delta'])), reverse=True)
    return {'tested': tested, 'strict_candidates': strict[:50]}


def graph_transitions(umax=7, rmax=10, hmax=1500):
    if nx is None:
        return {'worker': 'graph', 'claim_level': 'UNAVAILABLE', 'error': 'networkx unavailable'}
    G = nx.DiGraph(); states = []
    for u in range(1, umax + 1):
        for r in range(1, rmax + 1):
            for h in range(5, hmax + 1, 6):
                if admissible_state(u, r, h):
                    state = (u, r, h); states.append(state); G.add_node(state)
    by_ur = {}
    for b in states: by_ur.setdefault((b[0], b[1]), []).append(b)
    for a in states:
        for un in range(1, umax + 1):
            for rn in range(1, rmax + 1):
                for b in by_ur.get((un, rn), []):
                    if hcouples(a, b): G.add_edge(a, b)
    cyc = list(nx.simple_cycles(G))
    scc_nontrivial = [c for c in nx.strongly_connected_components(G) if len(c) > 1]
    self_loops = list(nx.selfloop_edges(G))
    edges = list(G.edges())
    rank_search = discover_ranks(edges)
    return {'worker': 'graph', 'claim_level': 'FINITE_GRAPH_SEARCH',
            'bounds': {'u': umax, 'r': rmax, 'h': hmax},
            'state_conditions': ['h>=5', 'h≡5 mod 6', 'v3(4^r h + 1)=u', 'exact H-coupling'],
            'nodes': G.number_of_nodes(), 'edges': G.number_of_edges(),
            'nontrivial_scc_count': len(scc_nontrivial), 'self_loops_count': len(self_loops),
            'cycles_count': len(cyc), 'cycles_preview': [list(map(list, c)) for c in cyc[:20]],
            'rank_search': rank_search,
            'rank_warning': 'Monotonicity on this finite graph is hypothesis discovery, not a universal proof.'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--worker', choices=['sympy', 'modular', 'z3', 'graph'], required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    fn = {'sympy': symbolic_identity, 'modular': modular_scan, 'z3': z3_hcoupling, 'graph': graph_transitions}[a.worker]
    result = fn()
    result['schema'] = 'cerebron-collatz-specialized-compute-v3'
    result['rule'] = 'Finite computation is evidence, not a universal Collatz proof.'
    with open(a.out, 'w') as f: json.dump(result, f, indent=2)
    print(json.dumps({k: result.get(k) for k in ('worker','claim_level','nodes','edges','cycles_count','solutions_count','admissible_state_count')}))

if __name__ == '__main__': main()
