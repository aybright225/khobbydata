from flask import Flask, request, render_template_string, redirect, jsonify
import json
import os
import requests
import uuid
from datetime import datetime

app = Flask(__name__)

ADMIN_PIN = "5329"
ORDERS_FILE = "orders.json"
PAYSTACK_SECRET = (os.environ.get("PAYSTACK_SECRET") or os.environ.get("PAYSTACK_SECRET_KEY") or "").strip()
PAYSTACK_PUBLIC = (os.environ.get("PAYSTACK_PUBLIC_KEY") or "").strip()
DATAPLAZA_BASE = "https://dataplazagh.com/api/v1"
DATAPLAZA_API_KEY = (os.getenv("DATAPLAZA_API_KEY") or "").strip()

# DataPlaza network_id: 1=MTN, 2=Telecel, 3=AT - your screenshot shows 3 but MTN is usually 1. We try 1.
MTN_NETWORK_ID = int(os.getenv("MTN_NETWORK_ID", "3"))

MTN_BUNDLES = [
    {"size": "1GB", "price": 4.7, "cap": 1, "valid": "90 days"},
    {"size": "2GB", "price": 9.6, "cap": 2, "valid": "90 days"},
    {"size": "3GB", "price": 14.5, "cap": 3, "valid": "90 days"},
    {"size": "4GB", "price": 19.4, "cap": 4, "valid": "90 days"},
    {"size": "5GB", "price": 24.0, "cap": 5, "valid": "90 days"},
    {"size": "6GB", "price": 28.5, "cap": 6, "valid": "90 days"},
    {"size": "8GB", "price": 37.5, "cap": 8, "valid": "90 days"},
    {"size": "10GB", "price": 47.0, "cap": 10, "valid": "90 days"},
    {"size": "15GB", "price": 69.5, "cap": 15, "valid": "90 days"},
    {"size": "20GB", "price": 93.2, "cap": 20, "valid": "90 days"},
]

def load_orders():
    if not os.path.exists(ORDERS_FILE):
        return []
    try:
        with open(ORDERS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_orders(orders):
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=2)

PAGE_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KhobbyBryt Data</title>
<style>
body{margin:0;background:#0f0f0f;color:#fff;font-family:Arial}
.header{background:#1a3cff;padding:14px 16px;display:flex;align-items:center}
.logo{display:flex;align-items:center;gap:10px;font-weight:800;font-size:19px}
.logo-icon{background:#fff;color:#1a3cff;width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:900}
.top{display:flex;justify-content:center;padding:14px 0 6px 0}
.mtn-tab{background:#ffcc00;color:#000;border:none;padding:9px 26px;border-radius:20px;font-weight:900;font-size:14px}
.meta{display:flex;gap:14px;justify-content:center;color:#9a9a9a;font-size:11px;padding:6px 0 10px 0}
.grid{padding-bottom:80px;display:flex;flex-direction:column;align-items:center}
.card{background:#ffcc00;color:#000;margin:8px auto;width:88%;max-width:300px;border-radius:18px;padding:14px;border:1.5px solid #000;box-sizing:border-box}
.card-top{display:flex;justify-content:space-between}
.tag{border:1.5px solid #000;border-radius:14px;padding:3px 10px;font-size:10px;font-weight:900}
.size{font-size:40px;font-weight:900;margin:10px 0 0 0;line-height:1}
.sub{margin:2px 0 0 0;font-weight:600;font-size:12px}
.price{font-size:22px;font-weight:900;margin-top:12px}
.valid{font-size:11px;font-weight:700;float:right;margin-top:-18px;background:#000;color:#ffcc00;padding:3px 8px;border-radius:10px}
.phone{width:100%;padding:12px;border-radius:10px;border:1.5px solid #000;margin-top:12px;box-sizing:border-box;font-size:15px;background:#fff;outline:none}
.buy{width:100%;background:#000;color:#ffcc00;border:none;padding:13px;border-radius:10px;font-weight:900;font-size:14px;margin-top:10px}
.wa{position:fixed;bottom:18px;right:14px;background:#25d366;color:#fff;width:52px;height:52px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:26px;text-decoration:none}
</style>
</head>
<body>
<div class="header"><div class="logo"><div class="logo-icon">K</div>KhobbyBryt Data</div></div>
<div class="top"><button class="mtn-tab">MTN • 90 Days</button></div>
<div class="meta"><span>10 bundles</span><span>• Instant</span><span>• Secure</span></div>
<div class="grid">
{% for b in bundles %}
<div class="card">
<div class="card-top"><span class="tag">MTN</span></div>
<div class="size">{{ b.size }}</div>
<div class="sub">MTN Bundle</div>
<div class="price">GHS {{ b.price }}</div><div class="valid">{{ b.valid }}</div>
<form action="/pay" method="post">
<input type="hidden" name="bundle" value="{{ b.size }}">
<input type="hidden" name="price" value="{{ b.price }}">
<input type="hidden" name="capacity" value="{{ b.cap }}">
<input class="phone" type="tel" name="phone" placeholder="0532738647" required>
<button class="buy" type="submit">Buy Now</button>
</form>
</div>
{% endfor %}
</div>
<a class="wa" href="https://wa.me/233532738647">💬</a>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(PAGE_HTML, bundles=MTN_BUNDLES)

@app.route("/pay", methods=["POST"])
def pay():
    phone = request.form.get("phone", "").strip()
    bundle = request.form.get("bundle", "1GB")
    capacity = request.form.get("capacity", "1")
    price = float(request.form.get("price", "4.8"))
    if not PAYSTACK_SECRET:
        return "<h3 style='text-align:center;font-family:Arial'>PAYSTACK_SECRET_KEY missing<br><a href='/'>Home</a></h3>"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}", "Content-Type": "application/json"}
    data = {"email": f"{phone}@khobbydata.com", "amount": int(price * 100), "metadata": {"phone": phone, "bundle": bundle, "capacity": capacity, "network": "MTN"}, "callback_url": f"{request.host_url}success"}
    r = requests.post("https://api.paystack.co/transaction/initialize", json=data, headers=headers, timeout=20)
    res = r.json()
    if res.get("status"):
        return redirect(res["data"]["authorization_url"])
    return f"Paystack error: {res} <a href='/'>Home</a>"

DATAPLAZA_BASE = "https://dataplazagh.com/api/v1"

def send_dataplaza(phone, gb):
    import requests, os
    key = os.getenv("DATAPLAZA_API_KEY","").strip()
    print(f"KEY CHECK len={len(key)}", flush=True)
    
    # Convert 1GB -> 1000, 2GB -> 2000 etc
    vol_mb = int(str(gb).replace("GB","").strip()) * 1000
    
    url = "https://dataplazagh.com/api/v1/orders"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
        "X-API-KEY": key,
        "x-api-key": key,
    }
    
    # SINGLE order format (not recipients array)
    payload = {
        "msisdn": phone,
        "volume_mb": vol_mb,
        "network_id": 1,  # 1=MTN
        # try also with network name
        "network": "MTN"
    }
    
    try:
        print(f"CALLING {url} {payload}", flush=True)
        r = requests.post(url, json=payload, headers=headers, timeout=20)
        print(f"FINAL {r.status_code} {r.text[:1000]}", flush=True)
        if r.status_code in [200,201]:
            return True, r.text
        else:
            return False, r.text
    except Exception as e:
        print(f"ERROR {e}", flush=True)
        return False, str(e)

@app.route("/success")
def success():
    ref = request.args.get("reference", "") or request.args.get("trxref", "")
    print(f"=== SUCCESS HIT ref={ref} ===", flush=True)
    
    if PAYSTACK_SECRET and ref:
        try:
            headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}"}
            vr = requests.get(f"https://api.paystack.co/transaction/verify/{ref}", headers=headers, timeout=20)
            vj = vr.json()
            print(f"Paystack verify: {vj}", flush=True)
            
            if vj.get("status") and vj["data"]["status"] == "success":
                meta = vj["data"]["metadata"]
                phone = meta.get("phone", "")
                capacity = meta.get("capacity", "1")
                bundle = meta.get("bundle", "1GB")
                
                # Normalize phone to 0xxxxxxxxx
                if phone.startswith("+233"):
                    phone = "0" + phone[4:]
                
                print(f"Calling DataPlaza phone={phone} cap={capacity} bundle={bundle}", flush=True)
                ok, resp = send_dataplaza(phone, capacity)
                print(f"DATAPLAZA FINAL -> ok={ok} resp={resp}", flush=True)

                orders = load_orders()
                orders.append({"time": datetime.now().isoformat(), "phone": phone, "capacity": capacity, "bundle": bundle, "dataplaza_ok": ok, "dataplaza_resp": str(resp)})
                save_orders(orders)
            else:
                print(f"Paystack NOT success: {vj}", flush=True)
        except Exception as e:
            print(f"SUCCESS ERROR {e}", flush=True)
            
    return "<div style='text-align:center;margin-top:80px;font-family:Arial'><h2>Payment successful! Data will arrive shortly.</h2><a href='/'>Go home</a></div>"

@app.route("/paystack/webhook", methods=["POST"])
def webhook():
    return jsonify({"status": "ok"}), 200

@app.route("/admin")
def admin():
    if request.args.get("pin") != ADMIN_PIN:
        return """<div style='text-align:center;margin-top:100px;font-family:Arial'><h2>Enter PIN</h2><input type='password' id='p' style='padding:10px'><br><br><button onclick="location.href='/admin?pin='+document.getElementById('p').value" style='padding:10px 20px'>Enter</button></div>"""
    orders = load_orders()
    total = sum(float(o.get("price", 0)) for o in orders)
    rows = "".join([f"<tr><td>{o.get('time','')[:19]}</td><td>{o.get('phone','')}</td><td>{o.get('bundle','')}</td><td>{o.get('price','')}</td></tr>" for o in reversed(orders)])
    return f"<body style='background:#111;color:#fff;font-family:Arial;padding:12px'><h3>{len(orders)} Orders | GHS {total}</h3><table border=1 style='border-collapse:collapse;width:100%;font-size:13px'><tr><th>Time</th><th>Phone</th><th>Bundle</th><th>Price</th></tr>{rows}</table></body>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
