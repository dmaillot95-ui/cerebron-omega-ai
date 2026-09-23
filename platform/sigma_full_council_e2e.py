from __future__ import annotations

import json
import pathlib

from sigma_manager import execute

OUT=pathlib.Path("platform/artifacts/sigma-full-council-e2e.json")


def main():
    result=execute(
        "Propose, critique and synthesize a bounded plan to improve CEREBRON memory routing. "
        "Preserve evidence limits and do not claim independent consensus.",
        full_council=True,
        max_new_tokens=48,
    )
    assert result["mode"]=="FULL_COUNCIL_8"
    assert len(result["selected_roles"])==8
    assert result["selected_roles"]==[
        "SAPHEA","SPIRALION","ETHERION","HYPERION",
        "ASTRION","METRION","AFAH","AELYS",
    ]
    assert len(result["role_results"])==8
    assert all(r["status"]=="EXECUTED" for r in result["role_results"])
    assert all(r["neural_independence"]=="SHARED_QWEN_CORRELATED" for r in result["role_results"])
    assert result["fusion"]["status"]=="EXECUTED"
    assert result["independent_general_neural_models"]==1
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({
        "status":"SIGMA_FULL_COUNCIL_8_EXECUTED",
        "roles":result["selected_roles"],
        "fusion_sha":result["fusion"]["output_sha"],
        "result_sha256":result["result_sha256"],
        "independent_general_neural_models":result["independent_general_neural_models"],
    }))


if __name__=="__main__":
    main()
