from flask import Flask, render_template, request, redirect
import os
import requests
import time

app = Flask(__name__)

PAYSTACK_SECRET = os.environ.get("PAYSTACK_SECRET_KEY")
PAYSTACK_PUBLIC = os.environ.get("PAYSTACK_PUBLIC_KEY")

DATAMART_API_KEY = "c3bb2d66891ca2dc895fd83acc484da89594b410071bb05911bf258ee515da97"
DATAMART_BASE = "https://api.datamartgh.shop/api/developer"

BUNDLES = [
    {"id":1, "network":"mtn", "data":"1GB", "price":4.70},
    {"id":2, "network":"mtn", "data":"2GB", "price":9.60},
    {"id":3, "network":"mtn", "data":"3GB", "price":14.50},
    {"id":4, "network":"mtn", "data":"4GB", "price":19.80},
    {"id":5, "network":"mtn", "data":"5GB", "price":24.00},
    {"id":6, "network":"mtn", "data":"6GB", "price":29.00},
    {"id":7, "network":"mtn", "data":"8GB", "price":37.00},
    {"id":8, "network":"mtn", "data":"10GB", "price":47.50},
    {"id":9, "network":"mtn", "data":"15GB", "price":70.00},
    {"id":10, "network":"mtn", "data":"20GB", "price":95.50}
]

def buy_from_datamart(phone, network, data_str):
    try:
        gb = int(data_str.replace("GB","").strip())
        headers = {"X-API-Key": DATAMART_API_KEY, "Content-Type": "application/json"}
        payload = {
            "ref": f"khobby-{int(time.time())}",
            "phone": phone,
            "network": network.lower(),
            "volume": gb
        }
        r = requests.post(f"{DATAMART_BASE}/purchase", json=payload, headers=headers, timeout=30)
        return r.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route('/')
def home():
    return render_template('index.html', bundles=BUNDLES, paystack_public=PAYSTACK_PUBLIC)

@app.route('/pay/<int:bid>', methods=["POST"])
def pay(bid):
    phone = request.form.get("phone")
    email = request.form.get("email") or "customer@khobby.com"
    bundle = next((b for b in BUNDLES if b["id"]==bid), None)
    if not bundle:
        return "Bundle not found", 404
    if not phone:
        return "Phone required", 400

    amount = int(float(bundle["price"]) * 100)
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}", "Content-Type": "application/json"}
    callback_url = f"{request.host_url}verify/{bundle['id']}/{phone}"
    
    data = {
        "email": email,
        "amount": amount,
        "callback_url": callback_url,
        "metadata": {"phone": phone, "bundle_id": bundle["id"], "bundle_data": bundle["data"]}
    }
    
    r = requests.post("https://api.paystack.co/transaction/initialize", json=data, headers=headers)
    j = r.json()
    if j.get("status"):
        return redirect(j["data"]["authorization_url"])
    return f"Paystack Error: {j}"

@app.route('/verify/<int:bundle_id>/<reference>')
def verify(bundle_id, reference):
    real_reference = request.args.get('reference', reference)
    if real_reference == reference: 
        phone = 'customer'
    else:
        phone = reference
        reference = real_reference

    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}"}
    try:
        r = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)
        data = r.json()
        if data.get('status') and data['data']['status'] == 'success':
            bundle = next((b for b in BUNDLES if b['id']==bundle_id), None)
            if phone == 'customer':
                phone = data['data']['metadata'].get('phone', phone)
            result = buy_from_datamart(phone, bundle['network'], bundle['data'])
            return f"""
            <div style="font-family:Arial;text-align:center;padding:40px">
            <h1 style="color:green">Payment Successful!</h1>
            <h2>{bundle['data']} for {phone}</h2>
            <p>Auto-delivery: {result}</p>
            <a href="/">Back Home</a>
            </div>
            """
    except Exception as e:
        print(e)
    return '<h1>Payment Failed</h1><a href="/">Try Again</a>'

if __name__=='__main__':
    port = int(os.environ.get("PORT",10000))
    app.run(host='0.0.0.0',port=port)
