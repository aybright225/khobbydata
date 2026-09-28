from flask import Flask, render_template, request, redirect
import os, requests, time

app = Flask(__name__)

PAYSTACK_SECRET = os.environ.get("PAYSTACK_SECRET_KEY")
PAYSTACK_PUBLIC = os.environ.get("PAYSTACK_PUBLIC_KEY")

# DATAMART AUTO-DELIVERY
DATAMART_API_KEY = "c3bb2d66891ca2dc895fd83acc484da89594b410071bb05911bf258ee515da97"
DATAMART_BASE = "https://api.datamartgh.shop/api/developer"

BUNDLES = [
    {"id":1, "network":"mtn", "data":"1GB", "price":4.80},
    {"id":2, "network":"mtn", "data":"2GB", "price":9.90},
    {"id":3, "network":"mtn", "data":"3GB", "price":14.70},
    {"id":4, "network":"mtn", "data":"4GB", "price":19.80},
    {"id":5, "network":"mtn", "data":"5GB", "price":24.50},
    {"id":6, "network":"mtn", "data":"6GB", "price":29.50},
    {"id":7, "network":"mtn", "data":"7GB", "price":34.00},
    {"id":8, "network":"mtn", "data":"8GB", "price":39.50},
    {"id":9, "network":"mtn", "data":"9GB", "price":44.00},
    {"id":10, "network":"mtn", "data":"10GB", "price":49.50}
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
        print(f"Buying from DataMart: {payload}")
        r = requests.post(f"{DATAMART_BASE}/purchase", json=payload, headers=headers, timeout=30)
        print(f"DataMart Response: {r.text}")
        return r.json()
    except Exception as e:
        print(f"DataMart Error: {e}")
        return {"status": "error", "message": str(e)}

@app.route('/')
def home():
    return render_template('index.html',
        bundles=BUNDLES,
        paystack_public=PAYSTACK_PUBLIC)

@app.route('/pay/<int:bid>', methods=["POST"])
def pay(bid):
    phone = request.form.get("phone")
    email = request.form.get("email") or "customer@khobby.com"
    bundle = next((b for b in BUNDLES if b["id"]==bid), None)
    
    if not bundle:
        return "Bundle not found", 404
    
    if not phone:
        return "Phone required", 400

    # Paystack amount in pesewas
    amount = int(float(bundle["price"]) * 100)
    
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}", "Content-Type": "application/json"}
    
    # Important: callback goes to verify with bundle_id and phone
    callback_url = f"{request.host_url}verify/{bundle['id']}/{phone}"
    
    data = {
        "email": email,
        "amount": amount,
        "callback_url": callback_url,
        "metadata": {
            "phone": phone,
            "bundle_id": bundle["id"],
            "bundle_data": bundle["data"]
        }
    }
    
    r = requests.post("https://api.paystack.co/transaction/initialize", json=data, headers=headers)
    j = r.json()
    print(f"Paystack Init: {j}")
    
    if j.get("status"):
        return redirect(j["data"]["authorization_url"])
    
    return f"Paystack Error: {j}"

@app.route('/verify/<int:bundle_id>/<reference>')
def verify(bundle_id, reference):
    # reference here is actually phone from callback_url trick, OR real reference if Paystack appends ?reference=
    # Let's get real reference from query param if present
    real_reference = request.args.get('reference', reference)
    # phone is in the URL path as reference in our callback trick, so we need to get it correctly
    # Our callback_url was /verify/{id}/{phone}, so 'reference' variable is phone number
    # Real paystack ref is in ?reference=
    
    # Try to parse: if reference is phone, then real_reference is paystack ref
    if real_reference == reference: 
        # Means paystack didn't append, so reference is paystack ref and phone is in metadata
        phone = request.args.get('phone', 'customer')
    else:
        phone = reference  # our trick: we put phone in path
        reference = real_reference

    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}"}
    try:
        r = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)
        data = r.json()
        print(f"Verify: {data}")
        
        if data.get('status') and data['data']['status'] == 'success':
            bundle = next((b for b in BUNDLES if b['id']==bundle_id), None)
            # If phone still not found, get from metadata
            if phone == 'customer' or len(phone) < 9:
                phone = data['data']['metadata'].get('phone', phone)
            
            # AUTO-DELIVER!
            result = buy_from_datamart(phone, bundle['network'], bundle['data'])
            
            return f"""
            <div style="font-family:Arial;text-align:center;padding:40px">
            <h1 style="color:green">Payment Successful!</h1>
            <h2>{bundle['data']} for {phone}</h2>
            <p style="color:green;font-weight:bold">✅ Auto-delivery started!</p>
            <p>DataMart: {result}</p>
            <p>Ref: {reference}</p>
            <a href="/">Back Home</a>
            </div>
            """
    except Exception as e:
        print(e)
    return '<h1>Payment Failed</h1><a href="/">Try Again</a>'

if __name__=='__main__':
    port = int(os.environ.get("PORT",10000))
    app.run(host='0.0.0.0',port=port)
