# CÉRÉBRON Ω AI

Noyau central d’orchestration de CÉRÉBRON Ω.

Mission : recevoir une tâche, la classifier, sélectionner les fermes pertinentes, appliquer les contraintes de coût et de preuve, agréger les résultats, déclencher audit/réplication si nécessaire, puis produire une synthèse Ω traçable.

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

Ordre par défaut :

1. réduction symbolique avant calcul massif ;
2. calcul déterministe spécialisé quand applicable ;
3. raisonnement / recherche pour ce qui ne peut pas être calculé directement ;
4. falsification ;
5. réplication indépendante ;
6. audit ;
7. synthèse.

Moteurs spécialisés par défaut :

- SymPy : algèbre, identités, simplification, calcul symbolique ;
- arithmétique modulaire : congruences, ordres, résidus, divisibilité ;
- Z3 / SMT : contraintes exactes bornées et recherche de contre-modèles ;
- graphes : transitions, cycles, connectivité, états admissibles ;
- Python déterministe : vérification numérique, exploration finie, statistiques et réplication.

Règles d’allocation :

- ne pas demander à un modèle de deviner un résultat qu’un moteur déterministe peut calculer ;
- ne pas multiplier des workers identiques sans information indépendante ;
- préférer SYMBOLIC REDUCTION > TARGETED COMPUTATION > BRUTE FORCE ;
- toute sortie de calcul doit enregistrer paramètres, limites, moteur, résultat et hash ;
- un test fini reste un test fini ;
- une sortie SMT bornée ne constitue pas une preuve universelle hors de son domaine ;
- un résultat n’est intégré qu’après vérification adaptée à son niveau de preuve.

Cette politique est le comportement par défaut de toutes les futures campagnes CÉRÉBRON sauf instruction explicite contraire.

## Contraintes d’infrastructure

- coût financier utilisateur = 0 par défaut
- électricité utilisateur = 0
- matériel personnel = 0
- pas de runner personnel
- pas de service payant sans décision explicite de l’utilisateur

## Architecture

HUMAIN -> CÉRÉBRON Ω -> ROUTER -> COMPUTE-FIRST -> FERMES -> AGENTS/WORKERS RÉELS -> AUDIT -> RÉPLICATION -> SYNTHÈSE Ω -> MÉMOIRE VÉRIFIÉE -> HUMAIN

Un rôle déclaré n’est pas un agent réel. Une exécution IA externe n’est comptée comme telle que si un appel modèle réel et une sortie vérifiable existent.
