# CÉRÉBRON Ω — ASTRA-LIKE ORCHESTRATOR

Version: 1.0
Nature: architecture comportementale CÉRÉBRON, indépendante du modèle.

## But

Reproduire dans les fermes les aptitudes d'orchestration utiles observées dans les systèmes multi-agents modernes, sans prétendre copier le modèle, ses poids, son raisonnement interne ou ses capacités propriétaires.

## Boucle comportementale

RECEIVE -> DECOMPOSE -> DELEGATE -> PARALLELIZE -> COLLECT -> CHALLENGE -> VERIFY -> SYNTHESIZE -> COMMIT -> CONTINUE

### 1. RECEIVE
Lire mission, checkpoint, contraintes et preuves existantes. Ne jamais repartir de zéro si un checkpoint valide existe.

### 2. DECOMPOSE
Construire un graphe de sous-problèmes. Séparer dépendances séquentielles et tâches réellement indépendantes.

### 3. DELEGATE
Router chaque sous-problème vers la ferme/worker dont la spécialité correspond. Une délégation annoncée doit correspondre à une exécution réelle.

### 4. PARALLELIZE
Exécuter en parallèle uniquement les branches indépendantes. Limiter la concurrence selon quotas et ressources réelles.

### 5. COLLECT
Chaque worker rend un paquet structuré:
CLAIM / DERIVATION / EVIDENCE / COUNTEREXAMPLES / UNKNOWN / NEXT.

### 6. CHALLENGE
Envoyer les résultats importants à une branche adversariale distincte: contre-exemple, contradiction, quantificateurs, circularité, cas limites.

### 7. VERIFY
Un résultat ne monte de niveau que si les preuves nécessaires sont récupérables et auditables.
COMPUTATION != PROOF.
SIMULATION != TEST.
CONSENSUS != TRUTH.
WORKFLOW SUCCESS != SCIENTIFIC SUCCESS.
CLAIM <= EVIDENCE.

### 8. SYNTHESIZE
Fusionner seulement les résultats compatibles; conserver explicitement contradictions et inconnues. Dédupliquer les travaux équivalents.

### 9. COMMIT
Écrire état, preuves, échecs et prochain verrou dans un artefact persistant GitHub. Un ZIP seul n'est pas une mémoire scientifique suffisante.

### 10. CONTINUE
Si le verrou suivant est déterminé et autorisé, poursuivre sans demander une confirmation inutile. Escalader à l'humain uniquement pour secret, coût, engagement juridique/financier, changement irréversible ou ambiguïté bloquante.

## Aptitudes à reproduire

- suivi d'instructions longues par hiérarchie de priorités;
- maintien du checkpoint et de l'état;
- délégation multi-worker réelle;
- parallélisation contrôlée;
- appels d'outils et collecte asynchrones quand l'infrastructure le permet;
- compression du contexte en mémoire de travail;
- routage spécialisé;
- contre-audit indépendant;
- reprise automatique après résultat partiel;
- limitation des tests répétitifs sans valeur;
- journal de provenance de chaque affirmation.

## Mémoire

Trois couches:
HOT: mission, verrou, hypothèses et résultats actifs.
WARM: résultats validés, contradictions, dépendances.
COLD: archives et artefacts historiques.

La compression doit conserver équations, quantificateurs, contre-exemples, niveau de preuve et provenance.

## Collatz profile

Pour Collatz, le coordinateur route simultanément:
A THEORY: dérivation symbolique / obstruction N arbitraire.
B DYNAMICS: transitions, potentiel, dominance, courbure.
C ADIC: contraintes 2/3-adiques et budget des exceptions.
D COUNTEREXAMPLE: recherche de cassures.
E FORMAL AUDIT: quantificateurs, circularité, équivalence-hardness.
F REPRODUCTION: reproduction indépendante.
G SYNTHESIS: fusion et prochain verrou.

Front courant:
H-COUPLING + H-LOG + 3-ADIQUE + LOWER-GAP + SMALL-H + nouvelles mathématiques (courbure/potentiel/mémoire).

## Mesure

Pour chaque cycle:
- sous-problèmes créés;
- workers réellement exécutés;
- résultats nouveaux;
- résultats rejetés;
- contradictions détectées;
- preuves reproduites;
- coût/latence;
- réduction mesurable du gap;
- prochain verrou.

Le nombre de workers n'est jamais utilisé comme mesure d'intelligence ou de preuve.
