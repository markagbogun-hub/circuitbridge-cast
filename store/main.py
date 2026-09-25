import os, sqlite3, hashlib, secrets, json, urllib.request
from pathlib import Path
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

try:
    import stripe
except Exception:
    stripe=None

ROOT=Path(__file__).resolve().parent
DB=ROOT/"store.db"; DOWNLOAD=ROOT/"downloads"; DOWNLOAD.mkdir(exist_ok=True)
LICENSE_API=os.getenv("CASTWISE_LICENSE_API","http://localhost:8000")
LICENSE_ADMIN=os.getenv("CASTWISE_LICENSE_ADMIN_KEY","")
STORE_SECRET=os.getenv("CASTWISE_STORE_SECRET","change-this")
PRICE_ID=os.getenv("STRIPE_PRICE_ID","")
INSTALLER_NAME=os.getenv("CASTWISE_INSTALLER_NAME","Castwise-Audio-Doctor-Setup.exe")

app=FastAPI(title="Castwise Customer Store",version="1.6.0")
app.add_middleware(SessionMiddleware,secret_key=STORE_SECRET,max_age=60*60*24*7)
templates=Jinja2Templates(directory=str(ROOT/"templates"))

def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS customers(
      id INTEGER PRIMARY KEY,email TEXT UNIQUE,created TEXT,last_login TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS licenses(
      id INTEGER PRIMARY KEY,customer_id INTEGER,license_id TEXT UNIQUE,expires TEXT,
      status TEXT,created TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS login_codes(
      id INTEGER PRIMARY KEY,email TEXT,code_hash TEXT,expires TEXT,used INTEGER DEFAULT 0)""")
    c.commit(); return c

def norm(email): return email.strip().lower()
def hash_code(code): return hashlib.sha256((code+STORE_SECRET).encode()).hexdigest()

def require_customer(request):
    cid=request.session.get("customer_id")
    if not cid: raise HTTPException(401,"Please log in.")
    c=db(); row=c.execute("SELECT * FROM customers WHERE id=?",(cid,)).fetchone(); c.close()
    if not row: raise HTTPException(401,"Session expired.")
    return row

@app.get("/",response_class=HTMLResponse)
def home(request:Request):
    return templates.TemplateResponse("index.html",{"request":request})

@app.post("/checkout")
def checkout(request:Request):
    if stripe is None: raise HTTPException(503,"Stripe not installed")
    stripe.api_key=os.getenv("STRIPE_SECRET_KEY","")
    if not PRICE_ID: raise HTTPException(503,"Stripe price not configured")
    host=str(request.base_url).rstrip("/")
    session=stripe.checkout.Session.create(
      mode="payment",line_items=[{"price":PRICE_ID,"quantity":1}],
      success_url=host+"/success?session_id={CHECKOUT_SESSION_ID}",
      cancel_url=host+"/",metadata={"product":"castwise-audio-doctor"})
    return RedirectResponse(session.url,status_code=303)

@app.get("/success",response_class=HTMLResponse)
def success(request:Request):
    return templates.TemplateResponse("success.html",{"request":request})

@app.get("/portal",response_class=HTMLResponse)
def portal(request:Request):
    customer=require_customer(request)
    c=db(); licenses=c.execute("SELECT * FROM licenses WHERE customer_id=? ORDER BY id DESC",(customer["id"],)).fetchall(); c.close()
    return templates.TemplateResponse("portal.html",{"request":request,"customer":customer,"licenses":licenses})

@app.get("/login",response_class=HTMLResponse)
def login(request:Request):
    return templates.TemplateResponse("login.html",{"request":request})

@app.post("/login")
def login_send(request:Request,email:str=Form(...)):
    email=norm(email); code=str(secrets.randbelow(900000)+100000)
    c=db()
    c.execute("INSERT INTO login_codes(email,code_hash,expires) VALUES(?,?,?)",
      (email,hash_code(code),(datetime.now(timezone.utc)+timedelta(minutes=10)).isoformat()))
    c.commit(); c.close()
    # Development mode displays the code. Production should email it through a transactional provider.
    request.session["pending_email"]=email
    if os.getenv("CASTWISE_DEV_LOGIN","1")=="1":
        request.session["dev_code"]=code
    return RedirectResponse("/verify",status_code=303)

@app.get("/verify",response_class=HTMLResponse)
def verify_page(request:Request):
    return templates.TemplateResponse("verify.html",{"request":request,"dev_code":request.session.get("dev_code")})

@app.post("/verify")
def verify(request:Request,code:str=Form(...)):
    email=request.session.get("pending_email")
    if not email: return RedirectResponse("/login",303)
    c=db(); row=c.execute("""SELECT * FROM login_codes WHERE email=? AND used=0
      ORDER BY id DESC LIMIT 1""",(email,)).fetchone()
    if not row: raise HTTPException(400,"Login code not found.")
    if datetime.fromisoformat(row["expires"])<datetime.now(timezone.utc): raise HTTPException(400,"Code expired.")
    if not secrets.compare_digest(row["code_hash"],hash_code(code)): raise HTTPException(400,"Invalid code.")
    c.execute("UPDATE login_codes SET used=1 WHERE id=?",(row["id"],))
    c.execute("INSERT OR IGNORE INTO customers(email,created) VALUES(?,?)",(email,datetime.now(timezone.utc).isoformat()))
    customer=c.execute("SELECT * FROM customers WHERE email=?",(email,)).fetchone()
    c.execute("UPDATE customers SET last_login=? WHERE id=?",(datetime.now(timezone.utc).isoformat(),customer["id"]))
    c.commit(); c.close()
    request.session.clear(); request.session["customer_id"]=customer["id"]
    return RedirectResponse("/portal",303)

@app.post("/logout")
def logout(request:Request):
    request.session.clear(); return RedirectResponse("/",303)

@app.post("/stripe/webhook")
async def webhook(request:Request):
    if stripe is None: raise HTTPException(503,"Stripe unavailable")
    payload=await request.body(); sig=request.headers.get("stripe-signature")
    try:
        event=stripe.Webhook.construct_event(payload,sig,os.getenv("STRIPE_WEBHOOK_SECRET",""))
    except Exception as e: raise HTTPException(400,str(e))
    if event["type"]=="checkout.session.completed":
        s=event["data"]["object"]; email=(s.get("customer_details") or {}).get("email")
        if email:
            # Issue a 365-day license through the private server-to-server API.
            body=json.dumps({"customer":email,"machine_id":"*","days":365}).encode()
            req=urllib.request.Request(LICENSE_API+"/v1/licenses/issue",data=body,
              headers={"Content-Type":"application/json","X-Admin-Key":LICENSE_ADMIN})
            try:
                with urllib.request.urlopen(req,timeout=10) as r: lic=json.loads(r.read())
                c=db(); c.execute("INSERT OR IGNORE INTO customers(email,created) VALUES(?,?)",
                                  (norm(email),datetime.now(timezone.utc).isoformat()))
                cust=c.execute("SELECT id FROM customers WHERE email=?",(norm(email),)).fetchone()
                c.execute("""INSERT OR IGNORE INTO licenses(customer_id,license_id,expires,status,created)
                  VALUES(?,?,?,?,?)""",(cust["id"],lic["license_id"],lic["expires"],"active",
                  datetime.now(timezone.utc).isoformat()))
                c.commit(); c.close()
            except Exception:
                # Production: queue the fulfillment job instead of silently dropping it.
                pass
    return {"received":True}

@app.get("/download/installer")
def installer(request:Request):
    require_customer(request)
    p=DOWNLOAD/INSTALLER_NAME
    if not p.exists(): raise HTTPException(404,"Installer is not available yet.")
    return FileResponse(p,filename=p.name,media_type="application/octet-stream")

@app.get("/download/license/{license_id}")
def license_download(request:Request,license_id:str):
    customer=require_customer(request)
    c=db(); row=c.execute("""SELECT * FROM licenses WHERE license_id=? AND customer_id=?""",
                          (license_id,customer["id"])).fetchone(); c.close()
    if not row: raise HTTPException(404,"License not found.")
    # Production: fetch signed payload from license server and stream a customer-specific file.
    payload={"product":"castwise-audio-doctor","license_id":license_id,
             "customer":customer["email"],"expires":row["expires"],
             "status":row["status"]}
    tmp=ROOT/f"license-{license_id}.json"; tmp.write_text(json.dumps(payload,indent=2))
    return FileResponse(tmp,filename=f"Castwise-License-{license_id}.json",
                        media_type="application/json")

@app.get("/health")
def health(): return {"ok":True,"service":"castwise-customer-store"}
