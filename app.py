from flask import Flask, request, render_template, redirect
import json
import os
from datetime import datetime

app = Flask(__name__)

ADMIN_PIN = "5329"
ORDERS_FILE = "orders.json"

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

@app.route('/')
def home():
    return render_template('index.html') if os.path.exists('templates/index.html') else "KhobbyData Live. Go to /admin?pin=5329"

@app.route('/paystack/webhook', methods=['POST'])
def paystack_webhook():
    data = request.get_json(silent=True) or {}
    print("WEBHOOK RECEIVED")
    try:
        if data.get('event') == 'charge.success':
            d = data.get('data', {}) or {}
            meta = d.get('metadata', {}) or {}
            phone = meta.get('phone')
            network = meta.get('network', 'mtn')
            bundle = meta.get('bundle', '1GB')
            if not phone:
                auth = d.get('authorization', {}) or {}
                phone = auth.get('mobile_money_number') or 'UNKNOWN'
                print(f"NO METADATA - Using payer number: {phone}")
            print(f"ORDER TO DELIVER: {phone} - {network} - {bundle}")
            order = {
                'time': d.get('paid_at') or str(datetime.now()),
                'phone': phone,
                'network': network,
                'bundle': bundle,
                'price': d.get('amount', 0) / 100,
                'reference': d.get('reference', '')
            }
            orders = load_orders()
            orders.append(order)
            save_orders(orders)
            with open("orders.txt", "a") as f:
                f.write(f"{phone} | {network} | {bundle} | {d.get('reference','')}\n")
    except Exception as e:
        print(f"WEBHOOK ERROR: {e}")
    return {"status": "ok"}, 200

@app.route('/admin')
def admin():
    pin = request.args.get('pin')
    if pin != ADMIN_PIN:
        return '<form style="text-align:center;margin-top:100px"><h1>Enter PIN</h1><input type="password" id="p"><button type="button" onclick="location.href=\'/admin?pin=\'+document.getElementById(\'p\').value">Go</button></form>'
    orders = load_orders()
    total = sum(float(o.get('price', 0)) for o in orders)
    rows = ""
    for o in orders[::-1]:
        rows += f"<tr><td>{o.get('time','')}</td><td>{o.get('phone','')}</td><td>{o.get('network','')}</td><td>{o.get('bundle','')}</td><td>{o.get('price','')}</td><td>{o.get('reference','')}</td></tr>"
    return f"<html><head><meta name='viewport' content='width=device-width'><style>body{{background:#121212;color:#fff;font-family:Arial;padding:20px}}table{{width:100%;border-collapse:collapse}}td,th{{border:1px solid #333;padding:8px}}</style></head><body><h2>KhobbyBryt Admin - {len(orders)} - GHS {total}</h2><table><tr><th>Time</th><th>Phone</th><th>Network</th><th>Bundle</th><th>Price</th><th>Ref</th></tr>{rows}</table></body></html>"

@app.route('/success')
def success():
    return "Payment successful!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
