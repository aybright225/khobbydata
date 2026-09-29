from flask import Flask, request, jsonify, render_template_string, redirect
import json
import os
import requests
from datetime import datetime

app = Flask(__name__)

# === CONFIG ===
ADMIN_PIN = "5329"
ORDERS_FILE = "orders.json"
PAYSTACK_SECRET = os.environ.get("PAYSTACK_SECRET", "").strip()

# Your 10 MTN bundles - exact as you said
MTN_BUNDLES = [
    {"size": "1GB", "price": 4.8, "valid": "90 days"},
    {"size": "2GB", "price": 9.7, "valid": "90 days"},
    {"size": "3GB", "price": 14.6, "valid": "90 days"},
    {"size": "4GB", "price": 19.5, "valid": "90 days"},
    {"size": "5GB", "price": 24.0, "valid": "90 days"},
    {"size": "6GB", "price": 29.0, "valid": "90 days"},
    {"size": "8GB", "price": 39.0, "valid": "90 days"},
    {"size": "10GB", "price": 49.5, "valid": "90 days"},
    {"size": "15GB", "price": 70.0, "valid": "90 days"},
    {"size": "20GB", "price": 95.0, "valid": "90 days"},
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

# === YOUR YELLOW DESIGN FROM YOUR PHOTO ===
PAGE_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KhobbyBryt Data</title>
<style>
body{margin:0;background:#0f0f0f;color:#fff;font-family:Arial}
.header{background:#2a4bff;padding:14px 16px;display:flex;justify-content:space-between;align-items:center}
.logo{display:flex;align-items:center;gap:10px;font-weight:bold;font-size:20px}
.logo-icon{background:#fff;color:#2a4bff;width:38px;height:38px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:900}
.top{display:flex;justify-content:center;padding:16px}
.mtn-tab{background:#ffcc00;color:#000;border:none;padding:10px 28px;border-radius:24px;font-weight:800}
.meta{display:flex;gap:18px;justify-content:center;color:#888;font-size:13px;padding-bottom:8px}
.card{background:#ffcc00;color:#000;margin:14px;border-radius:22px;padding:18px}
.card-top{display:flex;justify-content:space-between;align-items:center}
.tag{border:1.6px solid #000;border-radius:18px;padding:5px 12px;font-size:11px;font-weight:800}
.size{font-size:58px;font-weight:900;margin:12px 0 0 0;line-height:1}
.sub{margin:0;font-weight:600}
.price{font-size:34px;font-weight:900;margin-top:18px}
.valid{float:right;margin-top:-22px;font-size:13px;font-weight:600}
.phone{width:100%;padding:14px;border-radius:10px;border:1.6px solid #000;margin-top:14px;box-sizing:border-box;font-size:15px}
.buy{width:100%;background:#000;color:#ffcc00;border:none;padding:16px;border-radius:12px;font-weight:800;font-size:16px;margin-top:14px}
.wa{position:fixed;bottom:22px;right:18px;background:#25d366;color:#fff;width:58px;height:58px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:30px;text-decoration:none;box-shadow:0 4px 12px rgba(0,0,0,0.4)}
</style>
</head>
<body>
<div class="header"><div class="logo"><div class="logo-icon">K</div>KhobbyBryt</div><div>☀️</div></div>
<div class="top"><button class="mtn-tab">MTN</button></div>
<div class="meta"><span>10 bundles</span><span>⚡ Fast delivery</span><span>🛡️ Secure</span></div>
{% for b in bundles %}
<div class="card">
<div class="card-top"><span class="tag">MTN</span><span>▼</span></div>
<div class="size">{{ b.size }}</div>
<div class="sub">MTN Bundle</div>
<div class="price">¢{{ b.price }}</div><div class="valid">{{ b.valid }}</div>
<form action="/pay" method="post">
<input type="hidden" name="bundle" value="{{ b.size }}">
<input type="hidden" name="price" value="{{ b.price }}">
<input class="phone" type="tel" name="phone" placeholder="Enter MTN number e.g 0532738647" required>
<button class="buy" type="submit">Buy Now</button>
</form>
</div>
{% endfor %}
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
    price = float(request.form.get("price", "4.8"))
    if not PAYSTACK_SECRET:
        return f"<h3 style='font-family:Arial;text-align:center'>PAYSTACK_SECRET not set in Render. Test order saved: {phone} {bundle} GHS {price}<br><a href='/'>Home</a></h3>"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}", "Content-Type": "application/json"}
    data = {
        "email": f"{phone}@khobbydata.com",
        "amount": int(price * 100),
        "metadata": {"phone": phone, "bundle": bundle, "network": "mtn"},
        "callback_url": "https://khobbydata.onrender.com/success"
    }
    r = requests.post("https://api.paystack.co/transaction/initialize", json=data, headers=headers, timeout=20)
    res = r.json()
    if res.get("status"):
        return redirect(res["data"]["authorization_url"])
    return f"Paystack error: {res} <a href='/'>Home</a>"

@app.route("/paystack/webhook", methods=["POST"])
def webhook():
    payload = request.get_json(silent=True) or {}
    try:
        if payload.get("event") == "charge.success":
            d = payload.get("data", {})
            meta = d.get("metadata", {})
            phone = meta.get("phone") or d.get("customer", {}).get("email") or "UNKNOWN"
            order = {
                "time": datetime.now().isoformat(),
                "phone": phone,
                "bundle": meta.get("bundle", "1GB"),
                "network": "mtn",
                "price": d.get("amount", 0) / 100,
                "reference": d.get("reference", "")
            }
            orders = load_orders()
            orders.append(order)
            save_orders(orders)
    except Exception as e:
        print("webhook error", e)
    return jsonify({"status": "ok"}), 200

@app.route("/admin")
def admin():
    if request.args.get("pin") != ADMIN_PIN:
        return """<div style='text-align:center;margin-top:100px;font-family:Arial'>
        <h2>Enter PIN</h2><input type='password' id='p' style='padding:10px'>
        <button onclick="location.href='/admin?pin='+document.getElementById('p').value" style='padding:10px'>Enter</button></div>"""
    orders = load_orders()
    total = sum(float(o.get("price", 0)) for o in orders)
    rows = ""
    for o in reversed(orders):
        rows += f"<tr><td>{o.get('time','')[:19]}</td><td>{o.get('phone','')}</td><td>{o.get('bundle','')}</td><td>{o.get('price','')}</td></tr>"
    return f"<body style='background:#111;color:#fff;font-family:Arial;padding:12px'><h3>{len(orders)} Orders | GHS {total}</h3><table border=1 style='border-collapse:collapse;width:100%'><tr><th>Time</th><th>Phone</th><th>Bundle</th><th>Price</th></tr>{rows}</table></body>"

@app.route("/success")
def success():
    return "<div style='text-align:center;margin-top:100px;font-family:Arial'><h1>✅ Payment Successful</h1><p>Your data will be delivered soon</p><a href='/'>Home</a></div>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
