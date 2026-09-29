from flask import Flask, render_template, request, redirect
import os, requests, time, json
from datetime import datetime

app = Flask(__name__)

PAYSTACK_SECRET = os.environ.get("PAYSTACK_SECRET_KEY")
DATAMART_API_KEY = "d7b2427ac995deb13c8b5fa37d81c8967a6ba0222a649861bffd0f187c7a3f35"
DATAMART_BASE = "https://api.datamartgh.shop/api"
ADMIN_PIN = "5330"  # Change this to your own PIN

ORDERS_FILE = "orders.json"

BUNDLES = [
    {"id":1, "network":"mtn", "data":"1GB", "price":4.80},
    {"id":2, "network":"mtn", "data":"2GB", "price":9.60},
    {"id":3, "network":"mtn", "data":"3GB", "price":14.50},
    {"id":4, "network":"mtn", "data":"4GB", "price":19.80},
    {"id":5, "network":"mtn", "data":"5GB", "price":24.50},
    {"id":6, "network":"mtn", "data":"6GB", "price":29.50},
    {"id":7, "network":"mtn", "data":"8GB", "price":37.00},
    {"id":8, "network":"mtn", "data":"10GB", "price":48.50},
    {"id":9, "network":"mtn", "data":"15GB", "price":70.00},
    {"id":10, "network":"mtn", "data":"20GB", "price":91.50}
]

def load_orders():
    try:
        if os.path.exists(ORDERS_FILE):
            with open(ORDERS_FILE, "r") as f:
                return json.load(f)
    except: pass
    return []

def save_order(order):
    orders = load_orders()
    orders.insert(0, order)
    orders = orders[:200]  # keep last 200
    try:
        with open(ORDERS_FILE, "w") as f:
            json.dump(orders, f, indent=2)
    except Exception as e:
        print(f"Save error: {e}")

def buy_from_datamart(phone, network, data_str):
    try:
        gb = int(data_str.replace("GB","").strip())
        headers = {"X-API-Key": DATAMART_API_KEY, "Content-Type": "application/json"}
        payload = {"ref": f"khobby-{int(time.time())}", "phone": phone, "network": network.lower(), "volume": gb, "capacity":f"{gb}GB", "amount":gb}
        r = requests.post(f"{DATAMART_BASE}/purchase", json=payload, headers=headers, timeout=30)
        print(f"DATAMART_BASE RESPONSE:{r.text}")
        return r.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route('/')
def home():
    return render_template('index.html', bundles=BUNDLES)

@app.route('/pay/<int:bid>', methods=['GET','POST'])
def pay(bid):
    phone = request.form.get("phone")
    email = request.form.get("email") or "customer@khobby.com"
    bundle = next((b for b in BUNDLES if b["id"]==bid), None)
    if not bundle: return "Bundle not found", 404
    amount = int(float(bundle["price"]) * 100)
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}", "Content-Type": "application/json"}
    callback_url = f"{request.host_url}verify/{bundle['id']}/{phone}"
data = {
  "email": email,
  "amount": int(amount * 100),
  "metadata": {
    "phone": phone_number,   # 05330081932
    "network": network,      # mtn
    "bundle": bundle_name,   # 2GB
    "custom_fields": [
      {"display_name": "Phone Number", "variable_name": "phone", "value": phone_number},
      {"display_name": "Network", "variable_name": "network", "value": network}
    ]
  },
  "callback_url": "https://khobbydata.onrender.com/success"
}
r = requests.post("https://api.paystack.co/transaction/initialize", json=data, headers=headers)
j = r.json()
if j.get("status"):
    return redirect(j["data"]["authorization_url"])
return f"Paystack Error: {j}"

@app.route('/verify/<int:bundle_id>/<reference>')
def verify(bundle_id, reference):
    real_reference = request.args.get('reference', reference)
    phone = 'customer' if real_reference == reference else reference
    reference = real_reference if real_reference != reference else reference
    if phone != 'customer' and request.args.get('reference'):
        phone = reference
        reference = real_reference

    # For Paystack new flow: phone is in url path, reference in query
    # Fix: /verify/1/055xxxx -> reference is in query string
    qs_ref = request.args.get('reference')
    if qs_ref:
        reference = qs_ref

    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}"}
    try:
        r = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)
        data = r.json()
        if data.get('status') and data['data']['status'] == 'success':
            bundle = next((b for b in BUNDLES if b['id']==bundle_id), None)
            meta_phone = data['data']['metadata'].get('phone', '')
            if meta_phone: phone = meta_phone
            
            result = buy_from_datamart(phone, bundle['network'], bundle['data'])
            dm_status = str(result).lower()
            
            if "success" in dm_status or "sent" in dm_status or "delivered" in dm_status:
                status_text = "✅ DELIVERED"; color = "green"; short_status = "DELIVERED"
                msg = f"Your {bundle['data']} has been sent to {phone}!"
            elif "processing" in dm_status or "pending" in dm_status or "queue" in dm_status:
                status_text = "⏳ PROCESSING"; color = "orange"; short_status = "PROCESSING"
                msg = f"Your {bundle['data']} for {phone} is processing. Will arrive in 5-10 mins."
            else:
                status_text = "⚠️ RECEIVED"; color = "#2E6BFF"; short_status = "RECEIVED"
                msg = f"Payment received. Delivering {bundle['data']} to {phone}..."

            # SAVE ORDER
            save_order({
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "phone": phone,
                "bundle": bundle['data'],
                "price": bundle['price'],
                "ref": reference,
                "status": short_status,
                "datamart": str(result)[:500]
            })

            return f"""<div style="font-family:Arial;text-align:center;padding:30px;max-width:500px;margin:30px auto;background:white;color:#000;border-radius:20px">
            <h1 style="color:{color};font-size:32px">{status_text}</h1><h2 style="margin:15px 0">{bundle['data']} for {phone}</h2>
            <p style="font-size:18px;margin:20px 0">{msg}</p>
            <div style="background:#f5f5f5;padding:15px;border-radius:12px;text-align:left;font-size:13px;margin:20px 0;color:#333"><b>Ref:</b> {reference}<br><b>DataMart:</b> {result}<br><b>Phone:</b> {phone}</div>
            <a href="/" style="display:inline-block;padding:14px 28px;background:#000;color:#FFC800;border-radius:12px;text-decoration:none;font-weight:800">Back Home</a><br><br>
            <a href="https://wa.me/233533081932?text=My {bundle['data']} for {phone} is {status_text} - Ref {reference}" style="color:#25D366;font-weight:700">Chat us if not received</a></div>"""
    except Exception as e:
        print(e); return f'<h1>Error: {e}</h1><a href="/">Try Again</a>'
    return '<div style="text-align:center;padding:40px"><h1>Payment Failed ❌</h1><a href="/">Try Again</a></div>'

@app.route('/admin')
def admin():
    pin = request.args.get("pin", "")
    if pin != ADMIN_PIN:
        return '<form style="text-align:center;margin-top:100px"><h2>Enter Admin PIN</h2><input type="password" name="pin" placeholder="PIN"><button>Login</button></form>', 401
    
    orders = load_orders()
    total_sales = sum(float(o.get('price',0)) for o in orders)
    
    html = f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1"><title>Admin - KhobbyBryt</title>
    <style>body{{font-family:Arial;background:#121212;color:#fff;padding:10px}} .top{{background:#2E6BFF;padding:15px;border-radius:12px;display:flex;justify-content:space-between}} table{{width:100%;border-collapse:collapse;margin-top:15px;background:#1e1e1e;border-radius:12px;overflow:hidden}} th,td{{padding:10px;text-align:left;font-size:12px;border-bottom:1px solid #333}} th{{background:#000;color:#FFC800}} .delivered{{color:#00ff88}} .processing{{color:orange}} .badge{{padding:3px 8px;border-radius:10px;font-size:10px;font-weight:800}} </style></head><body>
    <div class="top"><div><h2>KhobbyBryt Admin</h2><p>{len(orders)} orders | GH¢ {total_sales:.2f} total</p></div><a href="/" style="color:#FFC800">Home</a></div>
    <table><tr><th>Time</th><th>Phone</th><th>Bundle</th><th>Price</th><th>Status</th><th>Ref</th></tr>
    """
    for o in orders:
        cls = "delivered" if "DELIVERED" in o.get('status','') else "processing"
        html += f"<tr><td>{o.get('time','')}</td><td>{o.get('phone','')}</td><td><b>{o.get('bundle','')}</b></td><td>¢{o.get('price','')}</td><td class='{cls}'><b>{o.get('status','')}</b></td><td style='font-size:10px'>{o.get('ref','')[:20]}...</td></tr>"
    html += "</table><br><p style='font-size:11px;color:#777'>Last 200 orders. Pin: ?pin=5330 | WhatsApp: 233533081932</p></body></html>"
    return html

@app.route('/paaystack/webhook', methods=['POST'])
def paystack_webhook():
    data = request.get_json(silent=True)
    print(f"PAYSTACK WEBHOOK RECEIVED: {data}")
    return jsonify({"status": "ok"}), 200

@app.route('/health')
def health():
    return "ok", 200

@app.route('/sitemap.xml')
def sitemap():
    return """<?xml version="1.0" encoding="UFT-8"?>
    <urlset xm1ns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url><loc>https://khobbydata.onrender.com/</loc><priority>1.0</priority><changefreq>daily</changefreq></url>
    </urlset>""", 200, {'Content-Type': 'application/xml'}

@app.route('/robots.txt')
def robots():
    return """User-agent: *
    Allow: /
    Sitemap: https://khobbydata.onrender.com/sitemap.xml""", 200, {'Content-Type':'text/plain'}
    
if __name__=='__main__':
    port = int(os.environ.get("PORT",10000))
    app.run(host='0.0.0.0',port=port)
