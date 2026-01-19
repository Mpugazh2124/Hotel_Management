from flask import Flask, render_template, request

app = Flask("hotel_mang")

@app.route('/enter-details', methods=['GET', 'POST'])
def enter_details():
    name = None
    address = None
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')
    return render_template('enter_details.html', name=name, address=address)
