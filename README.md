# CÉRÉBRON Ω AI

Noyau central d’orchestration de CÉRÉBRON Ω.

Mission : recevoir une tâche, la classifier, sélectionner les fermes pertinentes, appliquer les contraintes de coût et de preuve, agréger les résultats, déclencher audit/réplication si nécessaire, puis produire une synthèse Ω traçable.

## Invariants

- REALITY > COHERENCE
- EVIDENCE > CONFIDENCE
- CLAIM <= EVIDENCE
- VERIFY BEFORE COMMIT
- SIMULATION != TEST
- CONSENSUS != TRUTH
- AGENT COUNT != INTELLIGENCE
- UNKNOWN REMAINS UNKNOWN
- VERIFY THE VERIFIER

## Contraintes d’infrastructure

- coût financier utilisateur = 0 par défaut
- électricité utilisateur = 0
- matériel personnel = 0
- pas de runner personnel
- pas de service payant sans décision explicite de l’utilisateur

## Architecture

HUMAIN -> CÉRÉBRON Ω -> ROUTER -> FERMES -> AGENTS/WORKERS RÉELS -> AUDIT -> RÉPLICATION -> SYNTHÈSE Ω -> MÉMOIRE VÉRIFIÉE -> HUMAIN

Un rôle déclaré n’est pas un agent réel. Une exécution IA externe n’est comptée comme telle que si un appel modèle réel et une sortie vérifiable existent.
