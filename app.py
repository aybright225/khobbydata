from flask import Flask, render_template, request
import os, requests

app = Flask(__name__)

PAYSTACK_SECRET = os.environ.get("PAYSTACK_SECRET_KEY")
PAYSTACK_PUBLIC = os.environ.get("PAYSTACK_PUBLIC_KEY")

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

@app.route('/')
def home():
    return render_template('index.html',
    bundles=BUNDLES,
    paystack_public=PAYSTACK_PUBLIC)

@app.route('/verify/<int:bundle_id>/<reference>')
def verify(bundle_id, reference): 
    phone = request.args.get('phone', 'customer')
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}"}
    try:
        r = request.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers, timeout=10)
        data = r.json()
        if data.get('status') and data['data']['status'] == 'success':
            bundle = next((b for b in BUNDLES if b['id']==bundles_id), None)
            return f"""
            <div style="font-family:Arial;text-align:center;padding:40px">
            <h1  style="color:green">Payment Successful!</h1>
            <h2>{bundle['data']} for {phone}</h2>
            <p>Data will arrive in Few minutes</p>
            <p>Ref: {reference}</p>
            <a href="/">Back Home</a>
            </div>
            """
    except Exeption as e:
      print(e)
    return '<h1>Payment Failed</h1><a href="/">Try Again</a>'

if __name__=='__main__':
    app.run()
                   
                   
        
        
        
