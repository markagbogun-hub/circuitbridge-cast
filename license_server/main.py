import os, json, uuid, sqlite3, base64
from datetime import datetime, timezone, timedelta
from pathlib import Path
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

APP="castwise-audio-doctor"
DATA=Path(os.getenv("CASTWISE_LICENSE_DATA","./data")); DATA.mkdir(parents=True,exist_ok=True)
DB=DATA/"licenses.db"; KEY=DATA/"ed25519-private.pem"
ADMIN=os.getenv("CASTWISE_LICENSE_ADMIN_KEY","CHANGE-ME")

def conn():
    c=sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS licenses(
      id TEXT PRIMARY KEY, customer TEXT, machine_id TEXT, expires TEXT,
      status TEXT, created TEXT, payload TEXT)""")
    return c

def private_key():
    if KEY.exists():
        return serialization.load_pem_private_key(KEY.read_bytes(),password=None)
    k=Ed25519PrivateKey.generate()
    KEY.write_bytes(k.private_bytes(serialization.Encoding.PEM,
      serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
    return k

def sign(payload):
    raw=json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
    return base64.urlsafe_b64encode(private_key().sign(raw)).decode()

def signed_license(customer,machine_id,days):
    now=datetime.now(timezone.utc)
    payload={"product":APP,"customer":customer,"license_id":"LIC-"+uuid.uuid4().hex[:16].upper(),
             "machine_id":machine_id,"expires":(now+timedelta(days=days)).isoformat()}
    payload["signature"]=sign(payload)
    return payload

class Issue(BaseModel):
    customer:str
    machine_id:str="*"
    days:int=365

class Activate(BaseModel):
    license_id:str
    machine_id:str

app=FastAPI(title="Castwise License Server",version="1.4.0")

def admin_check(k):
    if not k or k!=ADMIN: raise HTTPException(401,"Admin authentication required")

@app.get("/health")
def health(): return {"ok":True,"service":"castwise-license-server"}

@app.post("/v1/licenses/issue")
def issue(x:Issue,x_admin_key:str|None=Header(None)):
    admin_check(x_admin_key)
    if not 1<=x.days<=3650: raise HTTPException(400,"Invalid duration")
    lic=signed_license(x.customer,x.machine_id,x.days)
    c=conn(); c.execute("INSERT INTO licenses VALUES(?,?,?,?,?,?,?)",
      (lic["license_id"],x.customer,x.machine_id,lic["expires"],"active",
       datetime.now(timezone.utc).isoformat(),json.dumps(lic)))
    c.commit(); c.close()
    return lic

@app.post("/v1/licenses/activate")
def activate(x:Activate):
    c=conn(); row=c.execute("SELECT payload,status FROM licenses WHERE id=?",(x.license_id,)).fetchone()
    c.close()
    if not row: raise HTTPException(404,"License not found")
    if row[1]!="active": raise HTTPException(403,"License is not active")
    lic=json.loads(row[0])
    if lic["machine_id"] not in ("*",x.machine_id): raise HTTPException(403,"Machine mismatch")
    if datetime.fromisoformat(lic["expires"])<=datetime.now(timezone.utc): raise HTTPException(403,"License expired")
    return lic

@app.get("/v1/licenses/{license_id}")
def status(license_id:str,x_admin_key:str|None=Header(None)):
    admin_check(x_admin_key)
    c=conn(); row=c.execute("SELECT payload,status FROM licenses WHERE id=?",(license_id,)).fetchone(); c.close()
    if not row: raise HTTPException(404,"License not found")
    return {"license":json.loads(row[0]),"status":row[1]}

@app.post("/v1/licenses/{license_id}/revoke")
def revoke(license_id:str,x_admin_key:str|None=Header(None)):
    admin_check(x_admin_key)
    c=conn(); n=c.execute("UPDATE licenses SET status='revoked' WHERE id=?",(license_id,)).rowcount; c.commit(); c.close()
    if not n: raise HTTPException(404,"License not found")
    return {"license_id":license_id,"status":"revoked"}
