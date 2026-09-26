#!/usr/bin/env python3
import json
from pathlib import Path

PATH = Path('config/farms.json')
data = json.loads(PATH.read_text(encoding='utf-8'))

entries = [
  {
    'id': 175,
    'repo': 'cerebron-farm-175-weight-simulation',
    'domain': 'weight-simulation-candidate-ranking',
    'status': 'SIMULATION_AUDIT_PASS_NOT_TRAINED',
    'type': 'WEIGHT_SIMULATION_FARM',
    'training_status': 'NOT_TRAINED',
    'simulation_only': True,
    'weights_changed': False,
    'repository_exists': True,
    'repository_initialized': True,
    'evidence': {
      'audit_run_id': 36245028961,
      'dedicated_repo_head': 'e4a45307fa3c1d593110eb1f4c4ebade00b99b83',
      'claim_boundary': 'SIMULATION_NE_TRAINING'
    }
  },
  {
    'id': 176,
    'repo': 'cerebron-farm-176-nova-tricore',
    'domain': 'nova-tricore-parallel-exploration-invention-synthesis',
    'identity': 'NOVA',
    'status': 'MUTED_HOLD_NOT_TRAINED',
    'type': 'AI_FARM_TRI_CORE',
    'role': 'parallel exploration, invention and representation synthesis',
    'core_count': 3,
    'training_status': 'NOT_TRAINED',
    'weights_changed': False,
    'runtime_enabled': False,
    'output_enabled': False,
    'repository_exists': True,
    'repository_initialized': True,
    'dedicated_repo_head': '06b22e0e2fe5d97ff4795f15555b290afa17d6cd',
    'integration_contract': 'config/tricore-agora-memory-integration-v1.json'
  },
  {
    'id': 177,
    'repo': 'cerebron-farm-177-atlas-tricore',
    'domain': 'atlas-tricore-knowledge-integration-memory-transfer',
    'identity': 'ATLAS',
    'status': 'MUTED_HOLD_NOT_TRAINED',
    'type': 'AI_FARM_TRI_CORE',
    'role': 'parallel knowledge mapping, integration, memory continuity and transfer',
    'core_count': 3,
    'training_status': 'NOT_TRAINED',
    'weights_changed': False,
    'runtime_enabled': False,
    'output_enabled': False,
    'repository_exists': True,
    'repository_initialized': True,
    'dedicated_repo_head': '22a916281513b5c74dcfdec805acd6d57a911897',
    'integration_contract': 'config/tricore-agora-memory-integration-v1.json'
  },
  {
    'id': 178,
    'repo': 'cerebron-farm-178-colossus-tricore',
    'domain': 'colossus-tricore-difficult-reasoning-verification-synthesis',
    'identity': 'COLOSSUS',
    'status': 'MUTED_HOLD_NOT_TRAINED',
    'type': 'AI_FARM_TRI_CORE',
    'role': 'parallel difficult reasoning, verification and large-scale synthesis',
    'core_count': 3,
    'training_status': 'NOT_TRAINED',
    'weights_changed': False,
    'runtime_enabled': False,
    'output_enabled': False,
    'repository_exists': True,
    'repository_initialized': True,
    'dedicated_repo_head': '604514207afe221fa202f703c70397701b6223a7',
    'integration_contract': 'config/tricore-agora-memory-integration-v1.json'
  }
]

existing_low = [f for f in data['farms'] if int(f['id']) < 175]
existing_high = [f for f in data['farms'] if int(f['id']) > 178]
if existing_high:
    raise SystemExit('FAIL_CLOSED: farm ids above 178 already exist; manual reconciliation required')
data['farms'] = sorted(existing_low + entries, key=lambda x: int(x['id']))
data['max_farms'] = max(int(f['id']) for f in data['farms'])
data['version'] = '2.26'
policy = data.setdefault('policy', {})
policy['farm_cap'] = 178
policy['no_farm_above_178'] = False
policy['extension_farm_ids'] = sorted(set(policy.get('extension_farm_ids', []) + [175, 176, 177, 178]))
policy['extension_repository_initialized_ids'] = sorted(set(policy.get('extension_repository_initialized_ids', []) + [175, 176, 177, 178]))

PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('REGISTERED', [e['id'] for e in entries], 'max_farms=', data['max_farms'])
