import json
from pathlib import Path

PATH = Path('config/farms.json')

NEW = [
    (179, 'cerebron-farm-179-zeus-muse', 'ZEUS', 'muse-orchestration', 'multi-agent orchestration and decision fusion'),
    (180, 'cerebron-farm-180-poseidon-muse', 'POSEIDON', 'muse-complex-systems', 'complex-systems exploration and environment reasoning'),
    (181, 'cerebron-farm-181-hades-muse', 'HADES', 'muse-red-team', 'red-team failure analysis and extreme-case search'),
    (182, 'cerebron-farm-182-athena-muse', 'ATHENA', 'muse-reasoning-strategy', 'reasoning, strategy and proof-oriented analysis'),
    (183, 'cerebron-farm-183-apollo-muse', 'APOLLO', 'muse-science-synthesis', 'science, prediction and synthesis'),
    (184, 'cerebron-farm-184-artemis-muse', 'ARTEMIS', 'muse-targeted-research', 'autonomous targeted research and search'),
    (185, 'cerebron-farm-185-hermes-muse', 'HERMES', 'muse-tools-communication', 'tools, API and inter-AI communication'),
    (186, 'cerebron-farm-186-hephaestus-muse', 'HEPHAESTUS', 'muse-code-engineering', 'code, engineering and construction'),
    (187, 'cerebron-farm-187-aphrodite-muse', 'APHRODITE', 'muse-human-interface', 'human interaction, language and interface'),
    (188, 'cerebron-farm-188-ares-muse', 'ARES', 'muse-adversarial', 'adversarial hypothesis competition and stress testing'),
    (189, 'cerebron-farm-189-demeter-muse', 'DEMETER', 'muse-memory-consolidation', 'memory, knowledge continuity and consolidation'),
    (190, 'cerebron-farm-190-hera-muse', 'HERA', 'muse-governance-audit', 'governance, coordination and final audit'),
]

x = json.loads(PATH.read_text())
existing = {int(f['id']): f for f in x['farms']}

for farm_id, repo, identity, domain, role in NEW:
    if farm_id in existing:
        cur = existing[farm_id]
        if cur.get('repo') != repo:
            raise SystemExit(f'F{farm_id} already exists with another repo: {cur.get("repo")}')
        continue
    x['farms'].append({
        'id': farm_id,
        'repo': repo,
        'domain': domain,
        'identity': identity,
        'status': 'REPOSITORY_CREATED_EMPTY_NOT_TRAINED',
        'type': 'MUSE_STYLE_AI_FARM',
        'role': role,
        'architecture': 'PLAN_TOOL_OBSERVE_CORRECT_CONTINUE',
        'training_status': 'NOT_TRAINED',
        'weights_changed': False,
        'runtime_enabled': False,
        'output_enabled': False,
        'repository_exists': True,
        'repository_initialized': False,
        'agora_target': True,
        'memory_omega_target': True,
        'claim_boundary': 'MUSE_STYLE_ARCHITECTURE_NE_META_MUSE_WEIGHTS',
    })

x['farms'].sort(key=lambda f: int(f['id']))
x['max_farms'] = max(int(f['id']) for f in x['farms'])
policy = x.setdefault('policy', {})
policy['farm_cap'] = x['max_farms']
ids = set(policy.get('extension_farm_ids', []))
ids.update(range(179, 191))
policy['extension_farm_ids'] = sorted(ids)
empty = set(policy.get('extension_repository_empty_ids', []))
empty.update(range(179, 191))
policy['extension_repository_empty_ids'] = sorted(empty)
policy['no_farm_above_190'] = False
x['version'] = '2.27'

PATH.write_text(json.dumps(x, ensure_ascii=False, indent=2) + '\n')

# Fail closed validation.
y = json.loads(PATH.read_text())
by_id = {int(f['id']): f for f in y['farms']}
for farm_id, repo, *_ in NEW:
    assert by_id[farm_id]['repo'] == repo
    assert by_id[farm_id]['training_status'] == 'NOT_TRAINED'
    assert by_id[farm_id]['weights_changed'] is False
assert y['max_farms'] == 190
assert y['policy']['farm_cap'] == 190
print('REGISTER_MUSE_F179_F190=PASS')
