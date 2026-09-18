# CÉRÉBRON Ω — COLLATZ : CAMPAGNE MATHÉMATIQUES À CONSTRUIRE

## Mission

Ne plus chercher seulement une preuve de Collatz dans les cadres existants. Construire, tester, éliminer ou valider des objets mathématiques nouveaux spécifiquement adaptés à la dynamique accélérée

T(x) = (3x+1) / 2^{v2(3x+1)}

sur les entiers impairs positifs.

Ne jamais présenter une analogie physique comme une preuve mathématique.
Ne jamais importer une hypothèse du Paradigme Delta, du champ C, d'Etherion, des fractales ou du nombre d'or comme fait établi.
Ces paradigmes servent de GENERATEURS D'HYPOTHESES. Toute idée doit être redéfinie en objet arithmétique exact puis testée.

REALITY > COHERENCE
EVIDENCE > CONFIDENCE
CLAIM <= EVIDENCE
COMPUTATION != PROOF
ANALOGY != THEOREM
NEW VOCABULARY != NEW MATHEMATICS

## Objet d'état enrichi

Pour chaque étape impaire x_i, définir et étudier un état enrichi

S_i = (x_i, a_i, h_i, residues_i, gap_i, history_i)

avec a_i = v2(3x_i+1).

Les fermes doivent rechercher quelles composantes sont réellement nécessaires et supprimer les composantes sans pouvoir prédictif ou démonstratif.

## 8 domaines candidats à construire

### M1 — Géométrie arithmétique de trajectoire
Construire une géométrie intrinsèque du graphe Collatz.
Chercher distance, longueur, pente, courbure discrète et géodésiques arithmétiques.
Une « courbure » n'est admise que si elle possède une définition exacte et si elle apporte une inégalité nouvelle.

### M2 — Mécanique des contraintes Collatz
Traiter simultanément les contraintes de cycle, valuations, congruences, minimum de cycle, numérateurs de rotations et divisibilités.
Construire un espace de contraintes C_N et rechercher si son domaine admissible devient vide pour tout N>1.

### M3 — Théorie des dominances
Mesurer la compétition exacte entre croissance par 3 et contraction par 2^{a_i}.
Étudier les sommes A_N=sum a_i, les déficits/excès, small-h budget, lower-gap et leurs fluctuations locales.
Objectif : transformer une dominance moyenne en obstruction universelle, sans supposer que moyenne implique trajectoire individuelle.

### M4 — Courbure valuationnelle
Construire des dérivées discrètes des valuations :
Delta a_i=a_{i+1}-a_i,
Delta2 a_i=a_{i+2}-2a_{i+1}+a_i.
Tester si cycles ou trajectoires divergentes imposent des motifs de courbure incompatibles avec les congruences exactes.

### M5 — Champ de potentiel arithmétique
Chercher une fonction V(S) telle que sa variation sous T soit contrôlable.
Candidats : log x, corrections dépendant des résidus, valuations, mémoire finie et termes 3-adiques.
Cible forte : construire V avec dérive strictement négative hors d'un ensemble fini, ou démontrer pourquoi cette classe de potentiels est impossible.

### M6 — Mémoire causale arithmétique
Inspirée uniquement comme heuristique du Paradigme Delta / champ C : tester si une mémoire finie du mot de valuations ou des résidus rend visibles des contraintes absentes de l'état x seul.
Définir exactement la profondeur mémoire k et effectuer une ablation k=0,1,2,...
La mémoire n'est conservée que si elle produit un lemme ou une réduction vérifiable.

### M7 — Couplage multi-adique
Fusionner les contraintes 2-adiques, 3-adiques et modulaires dans un même objet.
Relier ce domaine aux fronts H-coupling, H-log et filtres 3-adiques existants.
Chercher une incompatibilité globale qui ne soit visible dans aucune projection prise séparément.

### M8 — Théorie de l'obstruction universelle
Fusion finale des domaines survivants.
Forme cible :
cycle/divergence supposé
=> contraintes exactes
=> domaine admissible réduit
=> invariant/dominance/courbure/couplage
=> contradiction.
La cible est N arbitraire, pas une simple extension N=5,6,7,...

## Mesure de l'effet de chaque invention mathématique

Chaque nouvel objet O doit produire une fiche d'effet :
1. définition exacte ;
2. unités/type mathématique ;
3. information nouvelle par rapport aux outils existants ;
4. contrainte ajoutée ;
5. réduction mesurable de l'espace admissible ;
6. cas éliminés ;
7. contre-exemples ;
8. dépendances ;
9. lemme candidat ;
10. niveau de preuve.

Score interdit si purement subjectif.
Mesurer plutôt :
- nombre/proportion de mots de valuations éliminés dans les expériences finies ;
- classes de congruence éliminées ;
- dimension/degrés de liberté supprimés ;
- bornes améliorées ;
- dépendance en N ;
- capacité de transfert de N fini vers N arbitraire.

## Routage des fermes

A_H_COUPLING : M2 + M7.
B_SMALL_H_BUDGET : M3 + M4.
C_LOWER_GAP : M1 + M3 + M5.
D_RED_TEAM : tenter de casser chaque définition, invariant, monotonie et implication.
E_FUSION : M6 + M8, déduplication, ablation, synthèse et promotion uniquement des résultats vérifiés.

Les autres fermes pertinentes servent à littérature, calcul symbolique, recherche de contre-exemples, réplication, formalisation, contradiction et preuve.

## Funnel d'invention

Générer beaucoup de constructions candidates, puis :
2000 idées brutes
-> fusion/déduplication
-> 500 définitions mathématiques exactes
-> 100 avec effet expérimental mesurable
-> 25 résistantes au Red Team
-> 6 familles avec lemme candidat
-> 3 programmes de preuve
-> 1 obstruction universelle candidate.

Aucun passage d'étape sans artefact vérifiable.

## Livrable central permanent

Le Hub doit maintenir :
- RESULTATS_ETABLIS
- NOUVEAUX_OBJETS
- EFFETS_MESURES
- CONTRE_EXEMPLES
- LEMMES_CANDIDATS
- LEMMES_VALIDES
- CONTRADICTIONS
- GAPS_RESTANTS
- TOP3_PROGRAMMES_PREUVE

Question directrice :
« Quel nouvel objet mathématique transforme le plus fortement la dynamique Collatz en contraintes exactes, et cet effet survit-il quand N devient arbitraire ? »
