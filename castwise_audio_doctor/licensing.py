import base64, hashlib, json, os, platform, uuid
from datetime import datetime, timezone
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

APP_ID="castwise-audio-doctor"; TRIAL_DAYS=14
# Replace with Castwise production public key after generating the server key.
CASTWISE_PUBLIC_KEY_B64=os.getenv("CASTWISE_PUBLIC_KEY_B64","")

def data_dir():
    p=Path(os.getenv("APPDATA",Path.home()))/"Castwise"/"AudioDoctor"; p.mkdir(parents=True,exist_ok=True); return p
def machine_id():
    raw=f"{platform.node()}|{platform.system()}|{platform.machine()}|{uuid.getnode()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32].upper()
def _trial_file(): return data_dir()/"trial.json"
def trial_status():
    from datetime import timedelta
    now=datetime.now(timezone.utc); p=_trial_file()
    if not p.exists():
        p.write_text(json.dumps({"started":now.isoformat(),"machine_id":machine_id()}),encoding="utf8")
        return {"active":True,"days_left":TRIAL_DAYS,"reason":"new_trial"}
    try:
        d=json.loads(p.read_text()); started=datetime.fromisoformat(d["started"])
        if d.get("machine_id")!=machine_id(): return {"active":False,"days_left":0,"reason":"machine_mismatch"}
        left=max(0,TRIAL_DAYS-int((now-started).total_seconds()//86400))
        return {"active":left>0,"days_left":left,"reason":"trial"}
    except Exception: return {"active":False,"days_left":0,"reason":"invalid_trial"}
def license_path(): return data_dir()/"license.json"
def verify_license(obj):
    req={"product","customer","license_id","machine_id","expires","signature"}
    if not req.issubset(obj) or obj["product"]!=APP_ID: return False,"Invalid license"
    if obj["machine_id"] not in ("*",machine_id()): return False,"Machine mismatch"
    if not CASTWISE_PUBLIC_KEY_B64: return False,"Production public key is not configured"
    sig=base64.urlsafe_b64decode(obj["signature"].encode())
    body={k:v for k,v in obj.items() if k!="signature"}
    raw=json.dumps(body,sort_keys=True,separators=(",",":")).encode()
    try: Ed25519PublicKey.from_public_bytes(base64.urlsafe_b64decode(CASTWISE_PUBLIC_KEY_B64)).verify(sig,raw)
    except Exception: return False,"Invalid license signature"
    if datetime.fromisoformat(obj["expires"].replace("Z","+00:00"))<=datetime.now(timezone.utc): return False,"License expired"
    return True,"Valid"
def install_license_file(path):
    try:
        obj=json.loads(Path(path).read_text(encoding="utf8")); ok,msg=verify_license(obj)
        if not ok:return False,msg
        license_path().write_text(json.dumps(obj,indent=2),encoding="utf8")
        return True,"License installed successfully."
    except Exception as e:return False,f"Could not install license: {e}"
def license_status():
    p=license_path()
    if p.exists():
        try:
            obj=json.loads(p.read_text()); ok,msg=verify_license(obj)
            if ok:return {"active":True,"reason":"licensed","customer":obj["customer"],"license_id":obj["license_id"],"expires":obj["expires"]}
        except Exception: pass
    return trial_status()
