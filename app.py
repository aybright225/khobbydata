from flask import Flask, render_template, request, redirect, jsonify
from models import db, Product, Sale
import os, requests
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
load_dotenv()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['UPLOAD_FOLDER']=os.path.join('static' , 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

with app.app_context():
    db.create_all()

PAYSTACK_SECRET = os.getenv("PAYSTACK_SECRET_KEY")
PAYSTACK_PUBLIC = os.getenv("PAYSTACK_PUBLIC_KEY")    

@app.route('/')
def dashboard():
    products = Product.query.all()
    return render_template('dashboard.html', products=products, paystack_public_key=PAYSTACK_PUBLIC)

@app.route('/')
def home():
    products = Product.query.all()
    return render_template('dashboard.html',products=products)

@app.route('/add',
methods=['GET','POST'])           
def add():
    if request.method == 'POST':
        name=request.form['name']
        qty=int(request.form['quantity']
)
        cost=float(request.form['cost_price'])
        sell=float(request.form['selling_price'])
        seller=request.form['seller_name']

        filename=None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename!='' and '.' in file.filename:
                if file.filename.rsplit('.',1) [1].lower() in ALLOWED_EXTENSIONS:
                  filename=secure_filename(file.filename)
                  file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))            

        p = Product(name=name, quantity=qty, cost_price=cost, selling_price=sell, image_filename=filename, seller_name=seller)
        db.session.add(p)
        db.session.commit()
        return redirect('/')
    return render_template('add_product.html')

@app.route('/pay/<int:id>', methods=['POST'])
def pay(id):
    p = db.session.get(Product, id)
    qty = int(request.form['qty'])
    email = request.form['email']
    amount = int(p.selling_price*qty*100)

    sale = Sale(product_id=p.id, product_name=p.name, quantity=qty, amount=p.selling_price*qty,  payment_method="Paystack-Momo", reference="", status="pending")
    db.session.add(sale)
    db.session.commit()

    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}"}
    data = {
        "email": email,
        "amount": amount,
        "currency": "GHS",
        "reference": f"sale_{sale.id}_{id}",
        "channels": ["mobile_money","card"],
        "callback_url": request.host_url + f"verify/ {sale.id}"
    }
    r = requests.post("https://api.paystack.co/transaction/initialize", headers=headers, json=data)
    res = r.json()
    if res['status']:
        sale.reference = res['data']['reference']
        db.session.commit()
        return redirect(res['data']['authorization_url'])
    return f"Paystack Error: {res}"

@app.route('/verify/<int:sale_id>')
def verify(sale_id):
    sale = db.session.get(Sale, sale_id)
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}"}
    r = requests.get(f"https://api.paystack.co/transaction/verify/{sale.reference}", headers=headers)
    res = r.json()
    if res['data']['status'] =='success':
        sale.status = 'success'
        product = db.session.get(Product, sale.product_id)
        if product:
            product.quantity -= sale.quantity
        db.session.commit()
        return f"<h1>Payment Successful! {sale.product_name} sold. GHS {sale.amount} via {res['data']['channel']}</h1><a href='/'>Back to Shop</a>"
    else:
        sale.status = 'failed'
        db.session.commit()
        return f"Payment failed. <a href='/'>Try Again</a>"

@app.route('/sell/<int:id>',
methods=['POST'])
def sell(id):
    p = Product.query.get(id)
    q = int(request.form['qty'])
    if p.quantity>=q:
        p.quantity -= q
        db.session.commit()
    return redirect('/')
if __name__ == '__main__': os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)    
app.run(host="0.0.0.0", port=10000)   
