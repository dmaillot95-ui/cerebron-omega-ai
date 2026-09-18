# CÉRÉBRON Ω AI

Noyau central d’orchestration de CÉRÉBRON Ω.

Mission : recevoir une tâche, la classifier, sélectionner les fermes pertinentes, appliquer les contraintes de coût et de preuve, agréger les résultats, déclencher audit/réplication si nécessaire, puis produire une synthèse Ω traçable.

## SPIRALIX Ω — langage inter-IA

SPIRALIX Ω est le langage symbolique compact commun de CÉRÉBRON, ARCHITECTON et SPIRALION. GLYPH-VECTOR Ω est sa couche machine d'encodage, vectorisation, indexation et routage.

Chaîne canonique :

SPIRALIX -> GLYPH-VECTOR -> JSON / langage naturel -> ROUTER -> COMPUTE-FIRST -> FERMES -> sorties réelles -> FALSIFICATION -> AUDIT -> RÉPLICATION -> SYNTHÈSE Ω.

Une IA n'a pas besoin d'avoir appris SPIRALIX : le routeur doit fournir une expansion JSON et/ou langage naturel sémantiquement équivalente. Les glyphes compressent les instructions mais ne créent ni capacité, ni agent, ni preuve supplémentaire.

## Invariants

- REALITY > COHERENCE
- EVIDENCE > CONFIDENCE
- CLAIM <= EVIDENCE
- VERIFY BEFORE COMMIT
- SIMULATION != TEST
- COMPUTATION != PROOF
- CONSENSUS != TRUTH
- AGENT COUNT != INTELLIGENCE
- UNKNOWN REMAINS UNKNOWN
- VERIFY THE VERIFIER

## Politique permanente COMPUTE-FIRST

Pour toute nouvelle tâche, CÉRÉBRON doit d’abord déterminer si une partie significative du problème est calculable de façon déterministe.

Ordre par défaut : réduction symbolique avant calcul massif ; calcul déterministe spécialisé ; raisonnement/recherche ; falsification ; réplication indépendante ; audit ; synthèse.

Moteurs spécialisés : SymPy, arithmétique modulaire, Z3/SMT, graphes et Python déterministe.

Règles : ne pas demander à un modèle de deviner un résultat calculable ; ne pas multiplier des workers identiques sans information indépendante ; préférer SYMBOLIC REDUCTION > TARGETED COMPUTATION > BRUTE FORCE ; enregistrer paramètres/limites/moteur/résultat/hash ; test fini != preuve universelle ; SMT borné != preuve hors domaine ; intégrer seulement après vérification adaptée.

## Contraintes d’infrastructure

- coût financier utilisateur = 0 par défaut
- électricité utilisateur = 0
- matériel personnel = 0
- pas de runner personnel
- pas de service payant sans décision explicite de l’utilisateur

## Architecture

HUMAIN -> CÉRÉBRON Ω -> SPIRALIX Ω -> ROUTER -> COMPUTE-FIRST -> FERMES -> AGENTS/WORKERS RÉELS -> AUDIT -> RÉPLICATION -> SYNTHÈSE Ω -> MÉMOIRE VÉRIFIÉE -> HUMAIN

Un rôle déclaré n’est pas un agent réel. Une exécution IA externe n’est comptée comme telle que si un appel modèle réel et une sortie vérifiable existent.
