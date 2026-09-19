# CÉRÉBRON Ω — Programme maître : Carte Spectrale Espace–Orientation
Version organisée après B1–B10

## Règle de séparation
Ne jamais mélanger les niveaux. Chaque résultat porte un statut:
K = mathématique classique connue
V = résultat vérifié dans notre construction
C = candidat à tester
N = candidat potentiellement nouveau, non revendiqué
P = hypothèse physique
A = application industrielle à valider

## AXE M0 — Données d'origine
Conserver séparément les observations utilisateur: origine O; projections sin/cos; quatre cercles (2 horizontaux, 2 verticaux); pas cos 36°; famille sin associée; angles 18,30,36,45,54,60,72,90,108,144,342,666°; extension évoquée à 16 cercles/8 paires; sphère XYZ; tore visuel; rotations sur axes différents.

## AXE M1 — Noyau 2D exact [K/V]
r=±2cos(theta), r=±2sin(theta).
Quatre cercles unité tangents à O.
Intersection orthogonale non nulle: (±1,±1), norme sqrt(2).
Ne pas ajouter de 3D ici.

## AXE M2 — Loi continue d'intersection [K/V]
Deux cercles égaux de rayon a, tangents à O, centres séparés de theta:
rho(theta)=2a cos(theta/2), 0<=theta<=pi.
Repères: theta=90° -> a sqrt(2); theta=72° -> a phi; theta=60° -> a sqrt(3).
Inverse: theta=2 acos(rho/(2a)).
But: classifier tout le spectre continu et les dégénérescences.

## AXE M3 — Spectre cyclotomique [K]
lambda_n=2cos(pi/n).
lambda_4=sqrt(2), lambda_5=phi, lambda_6=sqrt(3).
T_n(lambda_n/2)+1=0.
Traiter ceci comme contrôle classique, jamais comme nouveauté.

## AXE M4 — Composition/itération des cercles [C]
C'est le front principal de découverte.
Tester séparément: rotation; somme/Minkowski; produit complexe; inversion; composition; itération; graphe d'intersections.
Objectif: identifier l'opérateur exact qui reproduit l'extension utilisateur (dont 16 cercles) sans ajustement ad hoc.
Toute relation réductible à trigonométrie/Chebyshev/cyclotomie -> K, pas N.

## AXE M5 — Géométrie 3D [C]
Seulement après M4.
Relèvement XYZ avec matrices SO(3) ou quaternions.
Plusieurs axes et vitesses omega_i.
Mesurer: orbites, fermetures, quasi-périodicité, densité, symétries, intersections, invariants.
Ne pas confondre rotation de coordonnées et nouvelle dimension.

## AXE M6 — Tore / structures internes [C]
Dériver un tore uniquement si un cercle générateur est transporté sur une trajectoire circulaire:
x=(R+r cos v)cos u; y=(R+r cos v)sin u; z=r sin v.
Tester si le tore émerge de M4/M5; ne pas l'imposer.
Étudier rapports R/r et nombres d'enroulement.

## AXE M7 — Physique [P]
Isolé des mathématiques.
Champ magnétique, atomes, orbitales, chimie, ondes: seulement analogies tant qu'aucune équation dynamique + unités + prédiction falsifiable + benchmark expérimental.
Aucune ressemblance visuelle n'est une preuve physique.

## AXE M8 — Applications [A]
Seulement après invariant vérifié: cinématique multi-axes, trajectoires, robotique, mécanismes, traitement spectral, géométrie CAO, champs/ondes si modèle physique validé.
Exiger métrique d'avantage et benchmark.

## AXE M9 — Collatz [ISOLÉ]
Interlude conservé mais interdit dans la campagne principale.
Après fermeture de M4–M6, tester séparément si les valuations Collatz admettent un codage spectral préservant l'information et produisant une obstruction de cycle. Aucun transfert sans preuve.

## Orchestration 6 fonctions
A Formalisation: définitions/théorèmes.
B Alternatives: complexes, groupes, quaternions, topologie.
C Calcul: symbolique/numérique, recherche aveugle.
D Red Team: réduction aux résultats connus, contre-exemples.
E Audit: K/V/C/N/P/A + reproductibilité.
F Fusion: ne conserve que ce qui survit; aucune invention pendant fusion.

## Entonnoir de découverte
D0 observations -> D1 équations exactes -> D2 invariants -> D3 recherche aveugle -> D4 réduction au connu -> D5 contre-exemples -> D6 preuve -> D7 reproduction indépendante -> D8 nouveauté bibliographique -> D9 physique/applications.

## Prochaine priorité
1. B11: itération exacte de rho(theta) et graphe de fermetures.
2. B12: reconstruire la règle exacte des 16 cercles depuis les observations, sans hypothèse arbitraire.
3. B13: SO(3)/quaternions seulement sur les opérateurs survivants.
4. B14: topologie/tore émergent.
5. B15: audit de nouveauté.
