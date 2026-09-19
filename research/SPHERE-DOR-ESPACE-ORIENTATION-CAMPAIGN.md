# CEREBRON Ω — Campagne Sphere d'Or / Espace-Orientation

## Origine expérimentale
Construction utilisateur accumulée : projections polaires r=2 sin(theta) et r=2 cos(theta), avec les quatre branches ±sin, ±cos. En coordonnées polaires :
- r=2 cos(theta) => (x-1)^2+y^2=1
- r=-2 cos(theta) => (x+1)^2+y^2=1
- r=2 sin(theta) => x^2+(y-1)^2=1
- r=-2 sin(theta) => x^2+(y+1)^2=1
Ce sont quatre cercles unité tangents à O, deux horizontaux et deux verticaux.

Valeurs exactes à conserver :
2 sin(18°)=1/phi ; 2 cos(36°)=phi ; 2 sin(54°)=phi ;
2 cos(45°)=2 sin(45°)=sqrt(2) ;
2 cos(30°)=sqrt(3) ;
18°=pi/10, 36°=pi/5, 54°=3pi/10.
Angles observés : 18,30,36,45,54,60,72,90,108,144,342,666 degrés.
Ancienne extension : 16 cercles / 8 paires symétriques, diagonales et passage cercle -> sphere.

## Objet mathématique candidat
Définir une famille espace-orientation plutôt qu'une simple liste de valeurs :
C_{s,k}(theta) avec s in {sin,cos}, k in {+1,-1}, puis action de rotations 3D R in SO(3).
Étudier l'union, les intersections, enveloppes, orbites et invariants des cercles après relèvement dans R3/S2, puis une extension toroidale seulement si elle est mathématiquement nécessaire.

Coordonnées sphériques de référence :
x=r cos(beta) cos(alpha)
y=r cos(beta) sin(alpha)
z=r sin(beta)

## Questions scientifiques
Q1. Classifier exactement toutes les intersections des quatre cercles de base et expliquer l'apparition de sqrt(2).
Q2. Déterminer ce qui est spécifique à phi et ce qui découle seulement des identités trigonométriques classiques.
Q3. Construire la version 3D minimale : cercles orientés sur/dans une sphère, groupes de rotations, invariants.
Q4. Tester si la multiplication/itération des cercles génère réellement la rosace observée et identifier sa loi (groupe, harmonique, enveloppe, courbe algébrique).
Q5. Chercher une relation non triviale pi-phi-sqrt(2)-sqrt(3), en rejetant les simples réécritures trigonométriques.
Q6. Examiner seulement après validation mathématique les analogies avec champs magnétiques, tores, orbitales/atomes, chimie, ondes et ingénierie.

## Reality firewall
Une ressemblance visuelle n'est pas une identité.
Une identité trigonométrique connue n'est pas une découverte nouvelle.
Une analogie avec champ magnétique/atome n'est pas un modèle physique.
Une application industrielle exige un avantage mesurable sur un benchmark existant.
CLAIM <= EVIDENCE.

## Campagne six fonctions
A Construction : formalisation géométrique 2D/3D et fonction espace-orientation.
B Alternative : représentations complexes, quaternions, SO(3), Hopf/tore si pertinentes.
C Calcul : calcul symbolique + exploration numérique + classification intersections/orbites.
D Red Team : chercher équivalences connues, contre-exemples, artefacts de paramétrisation.
E Audit : distinguer identité connue / reformulation / résultat nouveau démontré.
F Fusion : conserver uniquement invariants et théorèmes survivants.

## Premier résultat exact
Les quatre équations de base ci-dessus sont déjà une structure fermée et testable. Les intersections diagonales des cercles adjacents satisfont x=y et donnent (hors O) (1,1), de norme sqrt(2). Les valeurs 2sin45°=2cos45°=sqrt(2) sont cohérentes avec cette diagonale, mais la coordonnée d'intersection et la longueur radiale doivent rester distinguées.

## Critère de découverte
Un candidat devient NOUVEAU seulement s'il fournit au moins un théorème/invariant non réductible immédiatement aux identités classiques, avec preuve ou contre-audit indépendant.