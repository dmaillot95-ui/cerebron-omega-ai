# CÉRÉBRON Ω — ORDRES CENTRAUX COLLATZ — 45 FERMES

Cadence cible : un cycle réseau toutes les 5 minutes.

Objectif réseau : viser 100 à 120 réponses IA externes RÉUSSIES au total par cycle pour l'ensemble des 45 fermes. Ce chiffre est une cible de capacité, pas une preuve mathématique et pas une garantie d'exécution.

Chaque ferme reçoit le checkpoint Collatz courant et travaille selon son domaine. Une ferme ne doit pas inventer une exécution. Toute contribution doit être reliée à une sortie réelle, un run, un artifact ou une réponse externe identifiable.

RÈGLE 55→1 PAR FERME

Chaque ferme doit organiser son travail en 55 passes numérotées P01→P55 dans UN SEUL paquet de sortie final. Ces 55 passes sont des unités de travail/analyse et ne doivent pas être comptées comme 55 appels externes supplémentaires sauf si le workflow les exécute réellement.

P01→P10 : compréhension du checkpoint, définitions, dépendances, invariants.
P11→P20 : dérivations nouvelles, factorisations, congruences, bornes, alternatives.
P21→P30 : recherche de contre-exemples, cas limites, mots imprimitifs, u=1, r=1, h=5/11/17, quantificateurs.
P31→P40 : réduction arithmétique, SYMBOLIC REDUCTION BEFORE MULTIPLICATION, cache/récurrences/congruences avant grands calculs, mesure des multiplications économisées.
P41→P47 : audit formel, circularité, EQUIVALENT-HARDNESS, finite-test firewall, indépendance des preuves.
P48→P52 : réplication indépendante et contradiction-resolution.
P53 : claims survivants uniquement.
P54 : RESIDUAL + blockers + inconnues.
P55 : message final de la ferme pour le hub.

FORMAT UNIQUE DU MESSAGE FINAL DE CHAQUE FERME

FARM-ID / DOMAIN / CYCLE / RUN-EVIDENCE / EXTERNAL-SUCCESS-COUNT / P01→P55 SUMMARY / VERIFIED / NARROWED / REJECTED / DUPLICATE / EQUIVALENT-HARDNESS / OPEN / COUNTEREXAMPLES / REPLICATION STATUS / ARITHMETIC SAVINGS / RESIDUAL / NEXTLOCK.

CENTRALISATION

Les 45 paquets de ferme sont remontés au hub central. Le hub ne fait pas de vote. Il déduplique, conserve les contradictions, exige audit + réplication et produit un seul paquet réseau pour A/B/C/D/E.

Pipeline : THEORY/DERIVATION → COUNTEREXAMPLE → FORMAL AUDIT → REPLICATION → CONTRADICTION RESOLUTION → UNKNOWN/GAP → CAPABILITY EVALUATION → SYNTHESIS.

Règles absolues : REALITY>COHERENCE ; EVIDENCE>CONFIDENCE ; CLAIM<=EVIDENCE ; COMPUTATION!=PROOF ; FINITE TEST!=UNIVERSAL PROOF ; WORKFLOW SUCCESS!=MODEL SUCCESS ; AGENT COUNT!=INTELLIGENCE ; CONSENSUS!=TRUTH ; VERIFY BEFORE COMMIT.
