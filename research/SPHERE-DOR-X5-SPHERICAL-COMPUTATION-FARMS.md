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
