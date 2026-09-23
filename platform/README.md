# CÉRÉBRON AI Platform MVP

Cockpit local, zéro coût par défaut, construit au-dessus des registres CÉRÉBRON existants.

```bash
python platform/server.py --port 8787
```

Puis ouvrir `http://127.0.0.1:8787`.

Le backend IA livré est un petit classifieur neuronal local réel (`CEREBRON-ROUTER-NN-V1`) exécuté sur CPU. Il sélectionne un domaine; il n'est pas présenté comme un LLM génératif. Les rôles CÉRÉBRON restent des rôles logiques tant qu'aucun modèle/adaptateur indépendant n'est lié et qualifié.

Tests :

```bash
python -m unittest discover -s platform/tests -v
```


## Real Farm Bridge V1

F123 is the first real farm bridge pilot. When `CEREBRON_GITHUB_TOKEN` is available to the local process, an orbital/Hohmann mission can commit a versioned request to the F123 repository, wait for the GitHub Actions worker, and return run/job/artifact/SHA evidence to the cockpit. Without the credential the control plane fails closed and reports `ROUTED_ONLY`; it never reports `FARM_EXECUTED` without the full evidence chain.
