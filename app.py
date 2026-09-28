@app.route('/verify/<int:bundle_id>/<reference>')
def verify(bundle_id, reference):
    phone = request.args.get('phone')
    print(f"NEW ORDER: {bundle_id} for {phone} Ref {reference}")
    return f:<h1>Paid! Data to {phone} will arrive in 5 minutes</h1>"
