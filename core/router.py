import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config" / "farms.json"

KEYWORDS = {
    "math": [9, 34, 35, 33],
    "physics": [10, 36, 37, 34],
    "chemistry": [11, 36, 37],
    "biology": [12, 37, 35],
    "health": [12, 34, 35],
    "energy": [14, 36, 37, 31],
    "space": [15, 13, 36, 37],
    "software": [17, 19, 20, 34],
    "ai": [18, 44, 45, 41, 34],
    "cyber": [19, 33, 34, 35],
    "finance": [21, 31, 33, 34],
    "business": [22, 31, 33],
    "law": [23, 34, 38],
    "policy": [24, 31, 33, 38],
    "climate": [26, 31, 36, 37],
    "agriculture": [27, 31, 36, 37],
    "education": [28, 30, 37, 41],
    "language": [29, 30, 35],
    "human": [30, 37, 41],
    "forecast": [31, 36, 33, 35],
    "invent": [32, 33, 34, 37],
    "counterexample": [33, 34, 35],
    "audit": [34, 35, 38],
    "replication": [35, 34, 41],
    "simulation": [36, 37, 34],
    "experiment": [37, 35, 34],
    "contradiction": [38, 33, 34],
    "unknown": [39, 33, 34],
    "memory": [40, 20, 34],
    "capability": [41, 34, 35],
    "orchestr": [42, 44, 45],
    "civilization": [43, 42, 38, 40],
    "platform": [44, 42, 45],
    "agent": [45, 18, 44, 42]
}


def load_registry():
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def route(question: str):
    registry = load_registry()
    by_id = {f["id"]: f for f in registry["farms"]}
    q = question.lower()
    scores = {}
    for key, ids in KEYWORDS.items():
        if key in q:
            for rank, farm_id in enumerate(ids):
                scores[farm_id] = scores.get(farm_id, 0) + (len(ids) - rank)
    if not scores:
        scores = {8: 3, 42: 2, 39: 1, 34: 1}
    ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
    selected = [by_id[i] | {"score": score} for i, score in ranked[:8] if i in by_id]
    return {
        "question": question,
        "selected_farms": selected,
        "rules": [
            "CLAIM<=EVIDENCE",
            "VERIFY_BEFORE_COMMIT",
            "UNKNOWN_REMAINS_UNKNOWN",
            "ROLE_IS_NOT_AGENT",
            "ZERO_USER_LOCAL_COMPUTE"
        ]
    }


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]).strip() or "general research question"
    print(json.dumps(route(question), ensure_ascii=False, indent=2))
