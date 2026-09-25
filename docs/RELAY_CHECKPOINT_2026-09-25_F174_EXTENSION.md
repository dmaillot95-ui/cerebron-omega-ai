# CÉRÉBRON ΑΩ — CHECKPOINT EXTENSION F174

Date : 2026-09-25  
Mode : REALITY / EVIDENCE / APPEND-ONLY

## Registre

- version : 2.25
- max_farms : 174
- farm_cap : 174
- F01→F172 : cristal historique préservé
- F173/F174 : extensions append-only
- constellation grecque : inchangée, 24 rôles jusqu'à F172

## F162 — NU

État réel :
- registre présent ;
- scaffold local présent et validé ;
- dépôt cible attendu : `dmaillot95-ui/cerebron-farm-162-nu` ;
- dépôt dédié : manquant ;
- entraînement : NOT_TRAINED ;
- déploiement : non revendiqué.

Statut :
`PREPARED_NOT_DEPLOYED_REPOSITORY_MISSING`

Scaffold :
`scaffolds/f162-nu`

## F173 — AÉLYS LIVE

Dépôt :
`dmaillot95-ui/cerebron-farm-173-aelys-live`

État réel :
- dépôt GitHub existe et possède une branche `main` ;
- base d'intégration F173 installée ;
- selftest dédié corrigé : SUCCESS, run `36155830169` ;
- HEAD vérifié : `1c296ae0ba430fc3706de7ad2d81a2a088ed613c` ;
- adaptateurs live/TikTok/TTS/avatar : UNQUALIFIED ;
- entraînement : NOT_TRAINED ;
- production live : NOT_DEPLOYED ;
- le bus maître `config/cerebron-unified-plugin-bus-v1.json` existe et son Guard est PASS ; le runtime des providers reste UNQUALIFIED.

Statut :
`BASE_INSTALLED_RUNTIME_ADAPTERS_UNQUALIFIED`

Scaffold :
`scaffolds/f173-aelys-live`

## F174 — ELYRA VISUAL SIMULATION

Dépôt :
`dmaillot95-ui/cerebron-farm-174-elyra-visual-simulation`

État réel :
- dépôt GitHub existe ;
- dépôt dédié actuellement vide / non initialisé ;
- scaffold local CÉRÉBRON présent et validé ;
- entraînement : NOT_TRAINED ;
- simulation visuelle exécutée : false ;
- test physique : NOT_TESTED.

Statut :
`PREPARED_NOT_DEPLOYED_REPOSITORY_EMPTY`

Scaffold :
`scaffolds/f174-elyra-visual-simulation`

## Preuves GitHub Actions

- F173 dépôt dédié Selftest corrigé : run 36155830169 — SUCCESS
- CÉRÉBRON Unified Plugin Bus Guard : run 36156083228 — SUCCESS
- F162/F173/F174 Reality Guard : run 36155160206 — SUCCESS
- CÉRÉBRON Omega Core : run 36155316250 — SUCCESS
- CÉRÉBRON Main Integration Gate : run 36155316281 — SUCCESS
- Civilization Crystal Baseline Guard : run 36155316425 — SUCCESS
- Greek AI Constellation Guard : run 36155137209 — SUCCESS

## Règles

Les dépôts F173/F174 existants ne doivent pas être confondus avec une capacité exécutée.

`REPOSITORY_EXISTS != REPOSITORY_INITIALIZED`

`SCAFFOLD_VALIDATED != RUNTIME_EXECUTED`

`VISUAL_SIMULATION != PHYSICAL_TEST`

`MEMORY != TRAINING`

`CLAIM <= EVIDENCE`

## Prochaine étape

F173 est déjà initialisée : ne pas la réinitialiser ni écraser son architecture dédiée.

Pour F173 :
1. qualifier séparément les adaptateurs live réels ;
2. résoudre/registrer le bus maître réel avant de déclarer un binding confirmé ;
3. ne jamais passer à LIVE/EXECUTED sans canary/run/artifact.

Pour F174, lorsqu'un outil pouvant initialiser un dépôt GitHub vide est disponible :
1. créer le premier commit ;
2. recopier ou réconcilier le scaffold canonique depuis le dépôt maître ;
3. exécuter le guard dédié ;
4. seulement après SUCCESS, passer `repository_initialized=true` ;
5. ne jamais confondre simulation visuelle et test physique.

Pour F162 :
- créer d'abord le dépôt dédié ;
- recopier `scaffolds/f162-nu` ;
- valider avant tout changement de statut.


## Correction de routage F173 → RDX

Le premier scaffold F173 associait à tort `rdx.search` / `rdx.fetch` à `F152_RDX`.

Vérification du registre maître :
- F152 = BETA ;
- F152 ne doit pas être utilisé comme fournisseur RDX.

Correction appliquée :
- provider : `RDX_EXCHANGE` ;
- dépôt : `dmaillot95-ui/cerebron-rdx-exchange` ;
- runtime : `UNBOUND` / non qualifié ;
- appels externes automatiques : false ;
- F152 est BETA et explicitement exclu du routage RDX.
