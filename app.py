from flask import Flask, request, jsonify, render_template_string, redirect
import json, os, requests
from datetime import datetime

app = Flask(__name__)
ADMIN_PIN = "5329"
ORDERS_FILE = "orders.json"

def get_secret(name1, name2):
    return os.environ.get(name1,"").strip() or os.environ.get(name2,"").strip()

PAYSTACK_SECRET = get_secret("PAYSTACK_SECRET_KEY","PAYSTACK_SECRET")
DATAPLAZA_KEY = get_secret("DATAPLAZA_API_KEY","DATAPLAZA_KEY")
DATAPLAZA_BASE = "https://dataplazagh.com/api/v1"
AUTO_DELIVERY = os.environ.get("AUTO_DELIVERY", "true").lower()== "true"

MTN_BUNDLES = [
    {"size":"1GB","price":4.8,"mb":1000},
    {"size":"2GB","price":9.7,"mb":2000},
    {"size":"3GB","price":14.6,"mb":3000},
    {"size":"4GB","price":19.5,"mb":4000},
    {"size":"5GB","price":24.0,"mb":5000},
    {"size":"6GB","price":29.0,"mb":6000},
    {"size":"8GB","price":39.0,"mb":8000},
    {"size":"10GB","price":49.5,"mb":10000},
    {"size":"15GB","price":70.0,"mb":15000},
    {"size":"20GB","price":95.0,"mb":20000},
]

def load_orders():
    if not os.path.exists(ORDERS_FILE): return []
    try:
        with open(ORDERS_FILE,"r") as f: return json.load(f)
    except: return []
def save_orders(o):
    with open(ORDERS_FILE,"w") as f: json.dump(o,f,indent=2)

DATAPLAZA_BASE = "https://dataplazagh.com/api/v1"

def deliver_to_dataplaza(phone, mb, network_id=3):
    if not AUTO_DELIVERY:
        return {"info": "Manual mode ON - not calling API"}
    
    if not DATAPLAZA_KEY:
        return {"error": "No DATAPLAZA_API_KEY in Render"}
    
    headers = {"x-api-key": DATAPLAZA_KEY, "Content-Type": "application/json"}
    phone = phone.replace("+233","0").strip()
    if phone.startswith("233"):
        phone = "0" + phone[3:]
    
    payload = {"network_id": network_id, "recipients": [{"msisdn": phone, "volume_mb": int(mb)}]}
    
    try:
        r = requests.post(f"{DATAPLAZA_BASE}/orders", json=payload, headers=headers, timeout=30)
        print(f"Dataplaza {r.status_code}: {r.text[:500]}")
        if r.status_code in [200,201,202]:
            return {"success": True, "code": r.status_code, "body": r.text[:500] or "Accepted"}
        try:
            return r.json()
        except:
            return {"error": r.text[:500], "code": r.status_code}
    except Exception as e:
        return {"error": str(e)}

PAGE_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>KhobbyBryt</title><style>
body{margin:0;background:#f5f5f5;color:#111;font-family:Arial}
*{box-sizing:border-box}
.header{background:#fff;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 1px 4px rgba(0,0,0,.1);position:sticky;top:0}
.store{font-weight:900;font-size:18px}
.badge{background:#ffcc00;padding:4px 10px;border-radius:20px;font-size:11px;font-weight:800}
.container{max-width:480px;margin:0 auto;padding:0 12px 80px}
.card{background:#ffcc00;border-radius:16px;padding:14px;margin:12px 0}
.net{border:1px solid #000;border-radius:12px;padding:3px 8px;font-size:10px;font-weight:800}
.size{font-size:34px;font-weight:900;margin-top:6px}
.price{font-size:22px;font-weight:900;margin-top:8px}
.valid{float:right;font-size:11px;font-weight:600;margin-top:10px}
.phone{width:100%;padding:12px;border-radius:10px;border:1.2px solid #000;margin-top:10px;display:block}
.buy{width:100%;background:#000;color:#ffcc00;border:none;padding:12px;border-radius:10px;font-weight:800;margin-top:8px}
.wa{position:fixed;bottom:16px;right:16px;background:#25D366;color:#fff;width:52px;height:52px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:28px;text-decoration:none}
</style></head><body>
<div class="header"><div class="store">KhobbyBryt</div><div class="badge">{{ bundles|length }} bundles • Fast</div></div>
<div class="container">
{% for b in bundles %}
<div class="card"><span class="net">MTN</span><div class="size">{{ b.size }}</div><div>MTN Bundle</div>
<div class="price">GH¢ {{ b.price }}</div><div class="valid">90 days</div>
<form action="/pay" method="POST"><input type="hidden" name="bundle" value="{{ b.size }}"><input type="hidden" name="price" value="{{ b.price }}"><input type="hidden" name="mb" value="{{ b.mb }}">
<input class="phone" name="phone" type="tel" placeholder="0532738647" required><button class="buy">Buy Now</button></form>
</div>
{% endfor %}
</div><a class="wa" href="https://wa.me/233532738647">💬</a></body></html>
"""

@app.route("/")
def home():
    return render_template_string(PAGE_HTML, bundles=MTN_BUNDLES)

@app.route("/pay", methods=["POST"])
def pay():
    phone = request.form.get("phone","").strip()
    bundle = request.form.get("bundle","1GB")
    price = float(request.form.get("price","4.8"))
    mb = int(request.form.get("mb","1000"))
    secret = PAYSTACK_SECRET or get_secret("PAYSTACK_SECRET_KEY","PAYSTACK_SECRET")
    if not secret or not secret.startswith("sk_"):
        return f"Paystack secret key missing or wrong. Found: {secret[:5]}... Go to /check",500
    headers = {"Authorization": f"Bearer {secret}", "Content-Type":"application/json"}
    data = {
        "email": f"{phone}@khobbydata.com",
        "amount": int(price*100),
        "currency": "GHS",
        "metadata": {"phone":phone,"bundle":bundle,"mb":mb,"network_id":3},
        "callback_url": "https://khobbydata.onrender.com/success"
    }
    r = requests.post("https://api.paystack.co/transaction/initialize", json=data, headers=headers, timeout=20)
    res = r.json()
    if res.get("status") and res["data"].get("authorization_url"):
        return redirect(res["data"]["authorization_url"])
    return f"Paystack error: {res} <a href='/'>Home</a>"

@app.route("/paystack/webhook", methods=["POST"])
def webhook():
    payload = request.get_json(silent=True) or {}
    if payload.get("event") == "charge.success":
        d = payload.get("data",{})
        meta = d.get("metadata",{})
        phone = meta.get("phone","")
        bundle = meta.get("bundle","")
        mb = int(meta.get("mb",1000))
        network_id = int(meta.get("network_id",3))
        
        # 1. Try to deliver via Dataplaza automatically
        plaza_res = deliver_to_dataplaza(phone, mb, network_id)
        
        order = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "phone": phone,
            "bundle": bundle,
            "mb": mb,
            "price": d.get("amount",0)/100,
            "reference": d.get("reference",""),
            "dataplaza_response": plaza_res,
            "status": "PAID - DELIVERED" if "error" not in str(plaza_res).lower() else "PAID - DELIVERY FAILED"
        }
        orders = load_orders()
        orders.append(order)
        save_orders(orders)
        print(f"Order: {order}")
    return jsonify({"ok":True})

@app.route("/check")
def check():
    ps = PAYSTACK_SECRET or get_secret("PAYSTACK_SECRET_KEY","PAYSTACK_SECRET")
    dp = DATAPLAZA_KEY or get_secret("DATAPLAZA_API_KEY","DATAPLAZA_KEY")
    return f"Paystack: len={len(ps)} ok={ps.startswith('sk_')} start={ps[:7]}<br>Dataplaza: len={len(dp)} ok={len(dp)>10} start={dp[:7]}...<br><br>If both ok, buying will auto-deliver!"

@app.route("/success")
def success():
    return "<div style='font-family:Arial;text-align:center;padding-top:60px'><h1>✅ Payment Successful</h1><p>We are sending your data now via Dataplaza</p><p>You will receive SMS shortly</p><a href='/'>Back to Store</a><br><br><a href='https://wa.me/233532738647'>Need help? WhatsApp</a></div>"

@app.route("/admin")
def admin():
    if request.args.get("pin") != ADMIN_PIN:
        return "<div style='text-align:center;margin-top:80px;font-family:Arial'><h3>PIN</h3><input id='p' type='password'><button onclick=\"location.href='/admin?pin='+document.getElementById('p').value\">Enter</button></div>"
    orders = load_orders()
    total = sum(o.get("price",0) for o in orders)
    rows = ""
    for o in reversed(orders):
        rows += f"<tr><td>{o.get('time')}</td><td>{o.get('phone')}</td><td>{o.get('bundle')}</td><td>{o.get('price')}</td><td>{str(o.get('dataplaza_response'))[:80]}</td><td>{o.get('status')}</td></tr>"
    return f"<div style='font-family:Arial;padding:10px'><h3>{len(orders)} Orders GH¢ {total}</h3><table border=1 style='width:100%;font-size:12px;border-collapse:collapse'><tr><th>Time</th><th>Phone</th><th>Bundle</th><th>Price</th><th>Dataplaza</th><th>Status</th></tr>{rows}</table></div>"

@app.route("/test-delivery")
def test_delivery():
    if request.args.get("pin") != "5329":
        return "Add ?pin=5329"
    phone = request.args.get("phone", "0532738647")  # your number
    mb = int(request.args.get("mb", "1000"))  # 1GB
    result = deliver_to_dataplaza(phone, mb, network_id=3)
    return jsonify({"phone": phone, "mb": mb, "AUTO": AUTO_DELIVERY, "result": result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
