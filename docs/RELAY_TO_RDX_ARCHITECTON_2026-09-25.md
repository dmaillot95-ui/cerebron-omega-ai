# CÉRÉBRON ΑΩ — RELAIS VERS ARCHITECTON / RDX

Date : 2026-09-25  
Mode : ZÉRO INTERFÉRENCE / R&D EXECUTION PLANE → RDX REGISTRY PLANE

## 0. Objet

Ce fichier informe l'IA qui travaille dans le dépôt maître CÉRÉBRON que le registre ARCHITECTON/RDX est désormais géré dans un dépôt séparé.

NE PAS interrompre les travaux R&D en cours.

NE PAS reconstruire RDX dans ce dépôt.

NE PAS modifier les fermes Collatz F01–F07.

## 1. Dépôt RDX

Dépôt indépendant :

`dmaillot95-ui/cerebron-rdx-exchange`

Le dépôt RDX contient :

- le registre canonique des 40 souches ARCHITECTON ;
- les 40 ordres M01 ;
- les 8 inboxes ;
- les Gates ;
- les schémas de handoff ;
- le registre d'objets ;
- le journal d'intégration ;
- les vues publiques du site.

## 2. Répartition des responsabilités

### ICI — CÉRÉBRON R&D EXECUTION PLANE

Continuer à :

- orchestrer les fermes et IA réellement disponibles ;
- effectuer la recherche ;
- produire les sources ;
- réaliser les architectures ;
- exécuter les calculs ;
- exécuter les simulations réellement disponibles ;
- préparer les tests ;
- rechercher les contradictions ;
- conduire Red Team et contre-audit ;
- produire M01→M06 ;
- préparer F01→F08 uniquement après le Gate approprié.

### RDX — REGISTRY / INTEGRATION PLANE

RDX :

- reçoit les handoffs ;
- valide les IDs ;
- contrôle provenance et preuves ;
- détecte doublons ;
- enregistre les décisions d'intégration ;
- maintient le registre canonique ;
- génère les vues du site ;
- normalise éventuellement vers les Decision Packs RDX.

## 3. Ne pas écrire directement dans le registre RDX

Une production R&D doit être transmise via un handoff.

Version actuelle :

`ARCHITECTON-RD-HANDOFF-1.1`

Template RDX :

`templates/architecton-rd-handoff-v1.json`

Contrat :

`docs/ARCHITECTON_RDX_INGEST_CONTRACT.md`

## 4. Où déposer

Dans le dépôt RDX :

`data/architecton/inbox/WAVE-01/`

jusqu'à :

`data/architecton/inbox/WAVE-08/`

La vague dépend de la souche.

Exemple :

S01 → WAVE-01  
S06 → WAVE-02  
S11 → WAVE-03  
S16 → WAVE-04  
S21 → WAVE-05  
S26 → WAVE-06  
S31 → WAVE-07  
S36 → WAVE-08

## 5. Priorité

Priorité initiale :

`WAVE-01 = S01 → S05`

Les 40 ordres M01 existent déjà dans RDX.

Ne pas les recréer ici.

## 6. Trace obligatoire

Pour toute IA / modèle / ferme réellement exécuté :

`EXEC-`

doit identifier au minimum :

- SOUCHE_ID
- FERME
- MODEL_OR_AGENT
- ROLE
- MISSION
- INPUT_HASH
- OUTPUT_HASH
- START
- END
- ARTIFACT
- STATUS

Un composant configuré mais non exécuté ne peut pas être déclaré EXECUTED.

## 7. Evidence

Dans ARCHITECTON utiliser :

`architecton_evidence_level`

Échelle :

E0 hypothèse / non vérifié  
E1 architecture / raisonnement  
E2 calcul analytique exécuté reproductible  
E3 simulation numérique exécutée vérifiée  
E4 test composant  
E5 test sous-système  
E6 démonstrateur intégré  
E7 environnement représentatif  
E8 historique opérationnel

Ne pas utiliser `evidence_level` comme synonyme.

RDX possède une sémantique distincte.

## 8. Séquence

M01
→ handoff
→ RDX Ingest Gate
→ Integration Proposal
→ décision d'intégration
→ APPROVED
→ M02

Puis :

M02 → M03 → M04 → M05 → M06

Après M06 :

PRE-R&D FREEZE
→ READY_FOR_F01_F08
→ F01→F08
→ ARCHITECTON_FROZEN
→ RDX normalization
→ RDX Evidence Gate
→ revue humaine
→ éventuelle publication.

## 9. Collision

Si un objet existe déjà dans RDX :

- le référencer ;
- ou proposer une nouvelle version ;
- ne pas créer de doublon silencieux.

UNE INFORMATION = UN ID = UNE SOURCE CANONIQUE.

## 10. Règles absolues

REALITY > COHERENCE  
EVIDENCE > CONFIDENCE  
CLAIM <= EVIDENCE  
VERIFY BEFORE COMMIT  
ABLATION BEFORE ADDITION  
SIMULATION != TEST  
MEMORY != TRAINING  
AGENT COUNT != INTELLIGENCE

Aucune source inventée.  
Aucun nombre inventé.  
Aucune simulation fictive.  
Aucun test fictif.  
Aucune ferme fictivement exécutée.  
Aucun agent fictivement exécuté.

## 11. Consigne finale

CONTINUE LES TRAVAUX R&D EN COURS.

Ce relais ne change pas les missions déjà actives.

Lorsqu'un résultat ARCHITECTON doit être enregistré pour le site RDX, produire un handoff 1.1 et le déposer dans l'inbox correspondante du dépôt RDX.

Le plan RDX se chargera ensuite de l'intégration sans reprendre la R&D.
