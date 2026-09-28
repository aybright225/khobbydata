from flask import Flask, request, render_template_string, redirect
import requests

app = Flask(__name__)

DATAMART_API_KEY = "c3bb2d66891ca2dc895fd83acc484da89594b410071bb05911bf258ee515da97"
DATAMART_URL = "https://datamart.com.gh/api/v2/bundle"

# YOUR BUNDLES - 14 bundles for MTN
BUNDLES = [
    {"id": 1, "network": "MTN", "gb": "1GB", "price": "4.90", "days": "90 days"},
    {"id": 2, "network": "MTN", "gb": "2GB", "price": "10.00", "days": "90 days"},
    {"id": 3, "network": "MTN", "gb": "3GB", "price": "14.50", "days": "90 days"},
    {"id": 4, "network": "MTN", "gb": "4GB", "price": "19.00", "days": "90 days"},
    {"id": 5, "network": "MTN", "gb": "5GB", "price": "24.00", "days": "90 days"},
    {"id": 6, "network": "MTN", "gb": "8GB", "price": "36.00", "days": "90 days"},
    {"id": 7, "network": "MTN", "gb": "10GB", "price": "44.00", "days": "90 days"},
    {"id": 8, "network": "MTN", "gb": "15GB", "price": "64.00", "days": "90 days"},
    {"id": 9, "network": "MTN", "gb": "20GB", "price": "84.00", "days": "90 days"},
    {"id": 10, "network": "MTN", "gb": "25GB", "price": "105.00", "days": "90 days"},
    {"id": 11, "network": "MTN", "gb": "30GB", "price": "124.00", "days": "90 days"},
    {"id": 12, "network": "MTN", "gb": "40GB", "price": "164.00", "days": "90 days"},
    {"id": 13, "network": "MTN", "gb": "50GB", "price": "204.00", "days": "90 days"},
    {"id": 14, "network": "MTN", "gb": "100GB", "price": "350.00", "days": "90 days"},
]

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>KhobbyBryt</title>
<style>
body { background:#121212; margin:0; font-family: -apple-system, sans-serif; color:#fff; }
.header { background:#2E6BFF; padding:15px; display:flex; justify-content:space-between; align-items:center; position:sticky; top:0; z-index:10; }
.logo { display:flex; align-items:center; gap:10px; font-weight:800; font-size:20px; }
.logo-k { background:#fff; color:#2E6BFF; width:36px; height:36px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:900; }
.tabs { display:flex; gap:8px; padding:15px; justify-content:center; }
.tab { padding:12px 20px; border-radius:12px; font-weight:700; border:none; }
.tab.active { background:#FFC800; color:#000; }
.tab.inactive { background:#2a2a2a; color:#777; }
.info { display:flex; gap:15px; justify-content:center; color:#888; font-size:13px; padding-bottom:10px; }
.cards { padding:12px; }
.wa { position:fixed; bottom:20px; right:20px; background:#25D366; width:55px; height:55px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:30px; z-index:99; }
</style>
</head>
<body>

<div class="header">
  <div class="logo"><div class="logo-k">K</div> KhobbyBryt</div>
  <div style="display:flex; gap:15px; font-size:22px;">☀️ ☰</div>
</div>

<div class="tabs">
  <button class="tab active">MTN</button>
  <button class="tab inactive">AirtelTigo</button>
  <button class="tab inactive">Telecel</button>
</div>

<div class="info">
  <span>14 bundles</span> <span>⚡ Fast delivery</span> <span>🛡️ Secure</span>
</div>

<div class="cards">
{% for b in bundles %}
<div style="background:#FFC800; border-radius:22px; padding:20px; margin-bottom:16px; color:#000;">
  <div style="display:flex; justify-content:space-between;">
    <div style="border:1.5px solid #000; border-radius:20px; padding:3px 12px; font-size:10px; font-weight:800;">{{b.network}}</div>
    <div style="background:rgba(0,0,0,0.12); width:30px; height:30px; border-radius:50%; display:flex; align-items:center; justify-content:center;">⌄</div>
  </div>
  <div style="font-size:44px; font-weight:900; color:#fff; margin-top:28px; line-height:1; text-shadow: 0 1px 0 rgba(0,0,0,0.1);">{{b.gb}}</div>
  <div style="font-size:14px; opacity:0.8; margin-top:2px;">{{b.network}} Bundle</div>
  <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-top:24px;">
    <div style="font-size:34px; font-weight:900;">¢{{b.price}}</div>
    <div style="font-size:13px; opacity:0.7;">{{b.days}}</div>
  </div>
</div>
{% endfor %}
</div>

<a href="https://wa.me/233000000000" class="wa">💬</a>

<script>
function fill(f,id){ 
  let phone=prompt("Enter phone number");
  if(!phone) return false;
  document.getElementById('p'+id).value=phone;
  return true;
}
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML, bundles=BUNDLES)

@app.route("/pay/<int:bid>", methods=["POST"])
def pay(bid):
    # Add your paystack/datamart logic here
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
