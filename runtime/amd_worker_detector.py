#!/usr/bin/env python3
import json,os,platform,shutil,subprocess,pathlib,hashlib

def cmd(a):
 try:return subprocess.run(a,capture_output=True,text=True,timeout=8).stdout.strip()
 except Exception:return ""

def exists(x):return shutil.which(x) is not None
cpu=platform.processor() or cmd(["bash","-lc","lscpu | grep 'Model name' | cut -d: -f2- | xargs"])
rocm=exists("rocminfo");hip=exists("hipcc");amd_smi=exists("amd-smi") or exists("rocm-smi")
rocminfo=cmd(["rocminfo"]) if rocm else ""
amd_gpu=("AMD" in rocminfo or "gfx" in rocminfo) if rocm else False
npu_nodes=[]
for p in ["/dev/accel","/dev/dri"]:
 if os.path.exists(p): npu_nodes.append(p)
lemonade=exists("lemonade") or exists("lemonade-server")
gaia=exists("gaia")
out={"schema":"cerebron.amd-worker.v1","host":platform.node(),"os":platform.platform(),"cpu":cpu,"capabilities":{"rocm":rocm,"hipcc":hip,"amd_smi":amd_smi,"amd_gpu_visible":amd_gpu,"device_nodes":npu_nodes,"lemonade":lemonade,"gaia":gaia},"routing":{"gpu_compute":bool(rocm and amd_gpu),"local_ai":bool(lemonade),"npu_inference":False},"policy":{"route_only_if_detected":True,"zero_paid_overage":True,"unknown_npu_fail_closed":True}}
raw=json.dumps(out,sort_keys=True).encode();out["sha256"]=hashlib.sha256(raw).hexdigest();pathlib.Path("artifacts").mkdir(exist_ok=True);pathlib.Path("artifacts/amd_worker_detector.json").write_text(json.dumps(out,indent=2)+"\n");print(json.dumps(out));
