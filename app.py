from flask import Flask, request, jsonify, render_template_string, redirect
import json, os, requests
from datetime import datetime

app = Flask(__name__)
ADMIN_PIN = "5329"
ORDERS_FILE = "orders.json"

MTN_BUNDLES = [
    {"size":"1GB","price":4.8,"valid":"90 days"},
    {"size":"2GB","price":9.7,"valid":"90 days"},
    {"size":"3GB","price":14.6,"valid":"90 days"},
    {"size":"4GB","price":19.5,"valid":"90 days"},
    {"size":"5GB","price":24.0,"valid":"90 days"},
    {"size":"6GB","price":29.0,"valid":"90 days"},
    {"size":"8GB","price":39.0,"valid":"90 days"},
    {"size":"10GB","price":49.5,"valid":"90 days"},
    {"size":"15GB","price":70.0,"valid":"90 days"},
    {"size":"20GB","price":95.0,"valid":"90 days"},
]

def load_orders():
    if not os.path.exists(ORDERS_FILE):
        return []
    try:
        with open(ORDERS_FILE,"r") as f:
            return json.load(f)
    except:
        return []

def save_orders(orders):
    with open(ORDERS_FILE,"w") as f:
        json.dump(orders,f,indent=2)

PAGE_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>KhobbyBryt</title><style>
body{margin:0;background:#0f0f0f;color:#fff;font-family:Arial}
.header{background:#2a4bff;padding:12px 14px;display:flex;align-items:center}
.logo{display:flex;gap:8px;font-weight:bold;font-size:18px;align-items:center}
.logo-icon{background:#fff;color:#2a4bff;width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:900}
.top{display:flex;justify-content:center;padding:12px}
.mtn-tab{background:#ffcc00;color:#000;border:none;padding:8px 22px;border-radius:20px;font-weight:800;font-size:13px}
.meta{display:flex;gap:14px;justify-content:center;color:#888;font-size:11px;padding-bottom:6px}
.card{background:#ffcc00;color:#000;margin:10px auto;border-radius:18px;padding:14px;max-width:320px;width:90%}
.tag{border:1.4px solid #000;border-radius:16px;padding:4px 10px;font-size:10px;font-weight:800}
.size{font-size:36px;font-weight:900;margin:8px 0 0 0;line-height:1}
.sub{font-size:13px;font-weight:600;margin:2px 0 0 0}
.price{font-size:26px;font-weight:900;margin-top:12px}
.valid{float:right;margin-top:-18px;font-size:11px;font-weight:600}
.phone{width:100%;padding:12px;border-radius:8px;border:1.4px solid #000;margin-top:10px;box-sizing:border-box;font-size:13px}
.buy{width:100%;background:#000;color:#ffcc00;border:none;padding:13px;border-radius:10px;font-weight:800;font-size:14px;margin-top:10px}
.wa{position:fixed;bottom:18px;right:14px;background:#25d366;color:#fff;width:50px;height:50px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:26px;text-decoration:none}
</style></head><body>
<div class="header"><div class="logo"><div class="logo-icon">K</div>KhobbyBryt</div></div>
<div class="top"><button class="mtn-tab">MTN</button></div>
<div class="meta"><span>10 bundles</span><span>⚡ Fast</span><span>🛡️ Secure</span></div>
{% for b in bundles %}
<div class="card"><div><span class="tag">MTN</span></div>
<div class="size">{{ b.size }}</div><div class="sub">MTN Bundle</div>
<div class="price">¢{{ b.price }}</div><div class="valid">{{ b.valid }}</div>
<form action="/pay" method="post">
<input type="hidden" name="bundle" value="{{ b.size }}">
<input type="hidden" name="price" value="{{ b.price }}">
<input class="phone" type="tel" name="phone" placeholder="0532738647" required>
<button class="buy" type="submit">Buy Now</button>
</form></div>
{% endfor %}
<a class="wa" href="https://wa.me/233532738647">💬</a>
</body></html>
"""

@app.route("/")
def home():
    return render_template_string(PAGE_HTML, bundles=MTN_BUNDLES)

@app.route("/pay", methods=["POST"])
def pay():
    phone = request.form.get("phone","").strip()
    bundle = request.form.get("bundle","1GB")
    price = float(request.form.get("price","4.8"))
    secret = os.environ.get("PAYSTACK_SECRET","").strip()
    if not secret or not secret.startswith("sk_"):
        return f"<div style='font-family:Arial;padding:20px'><h3>Paystack key invalid in Render</h3><p>Found: '{secret[:10]}...' length {len(secret)}</p><p>Go to Render -> Environment -> PAYSTACK_SECRET must be sk_live_... (secret, not public)</p><p><a href='/check'>Check /check</a> | <a href='/'>Home</a></p></div>"
    headers = {"Authorization": f"Bearer {secret}", "Content-Type": "application/json"}
    data = {
        "email": f"{phone}@khobbydata.com",
        "amount": int(price*100),
        "metadata": {"phone": phone, "bundle": bundle, "network": "mtn"},
        "callback_url": "https://khobbydata.onrender.com/success"
    }
    r = requests.post("https://api.paystack.co/transaction/initialize", json=data, headers=headers, timeout=20)
    res = r.json()
    if res.get("status") and res.get("data",{}).get("authorization_url"):
        return redirect(res["data"]["authorization_url"])
    return f"Paystack error: {res} <br><a href='/'>Home</a> <a href='/check'>/check</a>"

@app.route("/paystack/webhook", methods=["POST"])
def webhook():
    payload = request.get_json(silent=True) or {}
    try:
        if payload.get("event") == "charge.success":
            d = payload.get("data",{})
            meta = d.get("metadata",{})
            order = {
                "time": datetime.now().isoformat(),
                "phone": meta.get("phone","UNKNOWN"),
                "bundle": meta.get("bundle","1GB"),
                "network": "mtn",
                "price": d.get("amount",0)/100,
                "reference": d.get("reference",""),
                "status": "paid - pending_manual"
            }
            orders = load_orders()
            orders.append(order)
            save_orders(orders)
    except Exception as e:
        print(e)
    return jsonify({"status":"ok"}),200

@app.route("/admin")
def admin():
    if request.args.get("pin") != ADMIN_PIN:
        return "<div style='text-align:center;margin-top:100px;font-family:Arial'><h2>PIN</h2><input id='p' type='password' style='padding:10px'><button onclick=\"location.href='/admin?pin='+document.getElementById('p').value\" style='padding:10px'>Go</button></div>"
    orders = load_orders()
    total = sum(float(o.get("price",0)) for o in orders)
    rows = "".join([f"<tr><td>{o.get('time','')[:19]}</td><td>{o.get('phone','')}</td><td>{o.get('bundle','')}</td><td>{o.get('price','')}</td></tr>" for o in reversed(orders)])
    return f"<body style='background:#111;color:#fff;font-family:Arial;padding:12px'><h3>{len(orders)} Orders GHS {total}</h3><table border=1 style='width:100%;border-collapse:collapse'><tr><th>Time</th><th>Phone</th><th>Bundle</th><th>Price</th></tr>{rows}</table></body>"

@app.route("/success")
def success():
    return "<div style='text-align:center;margin-top:80px;font-family:Arial'><h1>✅ Payment Successful</h1><p>Data will be delivered</p><a href='/'>Home</a></div>"

@app.route("/check")
def check():
    s = os.environ.get("PAYSTACK_SECRET","")
    return f"KEY length={len(s)} start={s[:7]} end={s[-4:]} has_sk={s.startswith('sk_')}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
