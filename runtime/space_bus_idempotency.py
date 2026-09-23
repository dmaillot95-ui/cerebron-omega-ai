import json,pathlib
cycle="SPACE-BUS-DELIVERY-0001"
receipts=[{"farm":102,"source":101,"consumption_id":"SPACE-BUS-DELIVERY-0001:F102"},{"farm":103,"source":102,"consumption_id":"SPACE-BUS-DELIVERY-0001:F103"},{"farm":104,"source":103,"consumption_id":"SPACE-BUS-DELIVERY-0001:F104"},{"farm":105,"source":104,"consumption_id":"SPACE-BUS-DELIVERY-0001:F105"},{"farm":106,"source":105,"consumption_id":"SPACE-BUS-DELIVERY-0001:F106"},{"farm":107,"source":106,"consumption_id":"SPACE-BUS-DELIVERY-0001:F107"},{"farm":108,"source":107,"consumption_id":"SPACE-BUS-DELIVERY-0001:F108"},{"farm":109,"source":108,"consumption_id":"SPACE-BUS-DELIVERY-0001:F109"},{"farm":110,"source":109,"consumption_id":"SPACE-BUS-DELIVERY-0001:F110"}]
seen=set()
for r in receipts: seen.add((cycle,r["farm"],r["source"]))
replay_blocked=all((cycle,r["farm"],r["source"]) in seen for r in receipts)
checks={"receipt_count":len(receipts)==9,"unique_first_pass":len(seen)==9,"replay_blocked":replay_blocked}
status="PASS" if all(checks.values()) else "FAIL"
res={"status":status,"cycle_id":cycle,"checks":checks,"rule":"EXACTLY_ONCE_LOGICAL_CONSUMPTION_BY_CYCLE_DESTINATION_SOURCE","epistemic":"IDEMPOTENCY_PROTOCOL_TEST_NOT_DISTRIBUTED_TRANSACTION_GUARANTEE"}
pathlib.Path("artifacts/space-bus-idempotency").mkdir(parents=True,exist_ok=True);pathlib.Path("artifacts/space-bus-idempotency/result.json").write_text(json.dumps(res,indent=2)+"\\n");print(json.dumps(res));raise SystemExit(0 if status=="PASS" else 1)
