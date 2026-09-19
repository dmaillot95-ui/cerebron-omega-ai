# SPHERE D'OR — X5 SPHERICAL COMPUTATION FARMS

## Mission
Test whether the Sphere d'Or construction can expose reusable algebraic generators that reduce the number of independent multiplications in exact computation.

CLAIM <= EVIDENCE
COMPUTATION != PROOF
GEOMETRIC SYMMETRY != RANK REDUCTION
VERIFY BEFORE COMMIT

## X5.1 — Representation
Represent bilinear products as points/states in a spherical or hyperspherical coordinate system. Record rotations, reflections, intersections, orbit classes and shared invariants.

## X5.2 — Farm A: construction
Search for spherical encodings in which multiple bilinear terms belong to the same orbit or share a generator.

## X5.3 — Farm B: alternative decompositions
Search independently for factorisations and tensor decompositions suggested by the spherical orbit structure. Do not assume the geometric encoding lowers rank.

## X5.4 — Farm C: exact calculation
For every candidate reduction, expand symbolically and verify every coefficient. Count scalar multiplications, additions, transformations and reconstruction cost separately.

## X5.5 — Farm D: Red Team
Try to break each candidate using generic symbolic inputs, random exact integer/rational instances, degeneracies, field restrictions and hidden precomputation costs.

## X5.6 — Farm E: audit
Classify each result:
- representation only;
- reusable common factor;
- restricted-domain reduction;
- exact general reduction;
- unverified candidate.

## X5.7 — Farm F: fusion
Keep only candidates surviving exact reconstruction and Red Team. Preserve minority blockers and counterexamples.

## Primary benchmark
For matrix multiplication, write the bilinear map as a tensor decomposition

T = sum_(k=1)^r u_k tensor v_k tensor w_k.

The experiment searches for spherical orbit structure that can reduce the number r of independent bilinear multiplications, not merely redraw the same r terms.

## Compression metric
R_mult = M_classical / M_candidate

R_total = Cost_classical / Cost_candidate

A candidate is useful only if reconstruction and geometric transforms do not erase the multiplication saving.

## Deep hypothesis
A large family of apparent operations may be generated from a much smaller family of independent generators:

{C_1,...,C_N} -> {G_1,...,G_r} + cheap transforms, with r << N.

This is a hypothesis to falsify, not an established property of the Sphere d'Or.

## Success gates
G1: exact reconstruction.
G2: at least one independent multiplication eliminated.
G3: no hidden restriction unless explicitly classified.
G4: total operation cost measured.
G5: independent Red-Team replication.
G6: only then test scaling from one saved multiplication toward large shared-factor compression.

## Next experiment
Enumerate spherical orbit classes of bilinear terms, canonicalize equivalent forms, detect shared linear forms, synthesize candidate decompositions, expand them exactly, and reject every candidate that does not reproduce the original polynomial identically.

## X5.2 — Exact low-rank calibration

Before attacking the 4x4 frontier, calibrate the spherical detector on exact small bilinear maps.

### Calibration A — shared-factor identity
F = ab + ac = a(b+c).

Naive monomial count: 2 bilinear products.
Exact bilinear generator count after factorisation: 1.
Interpretation: two edges share the same left linear form a. This is a real multiplication saving, not a geometric analogy.

### Calibration B — 2x2 matrix multiplication
Use the classical 8-product expansion as the baseline and require the detector to rediscover a 7-product exact decomposition (Strassen-class behaviour) without being given that decomposition as a template.

The spherical layer may only propose equivalence classes/orbits. Exact symbolic expansion decides whether a proposed orbit merge is legal.

### Candidate canonical state
For m_k = L_k(x) R_k(y), store:
S_k = (normalize(L_k), normalize(R_k), sign/scale, orbit invariants).

Two terms can be grouped geometrically when their canonical states are related by an allowed symmetry, but they can share one bilinear multiplication only when the reconstructed polynomial identity remains exact.

### Search funnel
1. Build all linear forms occurring in the target bilinear map.
2. Canonicalize proportional forms.
3. Construct a bipartite graph L <-> R for products.
4. Detect repeated stars, rectangles, low-rank blocks and symmetry orbits.
5. Propose merged generators G_q = U_q(x)V_q(y).
6. Solve exact reconstruction coefficients for outputs.
7. Expand symbolically.
8. Reject on any nonzero residual coefficient.
9. Count multiplications and all extra arithmetic.
10. Send survivors to independent Red Team.

### Residual certificate
For target F and candidate F_hat define
Delta = F - F_hat.

PASS requires every symbolic coefficient of Delta to equal exactly zero. Numerical agreement alone is insufficient.

### X5.2 decision
The Sphere d'Or hypothesis earns its first computational evidence only if its orbit/canonicalization layer rediscovers a known exact compression without the compression being hard-coded. A new lower-rank claim requires a separate proof and independent reproduction.

## X5.3 next
Implement the detector on the shared-factor calibration and 2x2 matrix multiplication, then compare:
- baseline multiplication count;
- discovered generator count;
- total arithmetic count;
- exact residual;
- whether the discovery came from spherical structure or ordinary factorisation alone.
