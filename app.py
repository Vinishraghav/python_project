import firebase_admin
from firebase_admin import credentials, auth

cred = credentials.Certificate('firebase_config.json')
firebase_admin.initialize_app(cred)


from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Sample user (for demo login)
USERS = [
    {"username": "vinish523@gmail.com", "password": "vinish123", "role": "user"},
    {"username": "vinish523@gmail.com", "password": "vinish123", "role": "updator"}
]

# Sample data
VANS = [
    {"id": 1, "name": "Premium Tour Van", "price": 120, "seats": 8, "available": True},
    {"id": 2, "name": "Luxury Family Van", "price": 150, "seats": 12, "available": True},
    {"id": 3, "name": "Eco Adventure Van", "price": 90, "seats": 6, "available": True}
]

BOOKINGS = []

@app.route('/')
def welcome():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        # Check if credentials match
        user = next((u for u in USERS if u['username'] == username and u['password'] == password and u['role'] == role), None)
        
        if user:
            session['user'] = username
            session['role'] = role
            flash(f'Logged in as {role}', 'success')
            
            # Redirect based on role
            if role == 'user':
                return redirect(url_for('home'))  # Main booking page
            elif role == 'updator':
                return redirect(url_for('admin_dashboard'))  # Admin view
        else:
            flash('Invalid credentials or role', 'danger')
    
    return render_template('home.html')

from firebase_admin import auth
from flask import jsonify

@app.route('/verify', methods=['POST'])
def verify():
    try:
        id_token = request.json.get('idToken')
        decoded_token = auth.verify_id_token(id_token)
        session['user'] = decoded_token['email']
        session['uid'] = decoded_token['uid']
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# The admin route should be defined once.
@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'updator':
        flash("Access denied", "danger")
        return redirect(url_for('login'))
    return render_template('admin.html', vans=VANS)

@app.route('/signup')
def signup_page():
    return render_template('signup.html')

@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('welcome'))

@app.route('/home')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/vans')
def list_vans():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('vans.html', vans=VANS)

@app.route('/admin/add', methods=['GET', 'POST'])
def add_van():
    if session.get('role') != 'updator':
        flash("Access denied", "danger")
        return redirect(url_for('login'))
    if request.method == 'POST':
        new_van = {
            "id": max([v["id"] for v in VANS]) + 1 if VANS else 1,
            "name": request.form['name'],
            "price": int(request.form['price']),
            "seats": int(request.form['seats'])
        }
        VANS.append(new_van)
        flash("Van added successfully!", "success")
        return redirect(url_for('admin_dashboard'))
    return render_template('add_van.html')

@app.route('/admin/edit/<int:van_id>', methods=['GET', 'POST'])
def edit_van(van_id):
    if session.get('role') != 'updator':
        flash("Access denied", "danger")
        return redirect(url_for('login'))
    van = next((v for v in VANS if v["id"] == van_id), None)
    if not van:
        flash("Van not found", "danger")
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        van["name"] = request.form['name']
        van["price"] = int(request.form['price'])
        van["seats"] = int(request.form['seats'])
        flash("Van updated successfully!", "success")
        return redirect(url_for('admin_dashboard'))
    
    return render_template('edit_van.html', van=van)

@app.route('/admin/delete/<int:van_id>', methods=['POST'])
def delete_van(van_id):
    if session.get('role') != 'updator':
        flash("Access denied", "danger")
        return redirect(url_for('login'))
    global VANS
    VANS = [v for v in VANS if v["id"] != van_id]
    flash("Van deleted successfully!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/book', methods=['POST'])
def book():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    van_id = int(request.form['van_id'])
    start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
    end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
    passengers = int(request.form['passengers'])
    
    van = next((v for v in VANS if v['id'] == van_id), None)
    
    if van and van['available']:
        booking = {
            'van_id': van_id,
            'start_date': start_date,
            'end_date': end_date,
            'passengers': passengers,
            'total_price': van['price'] * (end_date - start_date).days
        }
        BOOKINGS.append(booking)
        flash('Booking successful!', 'success')
        return redirect(url_for('booking_confirmation', booking_id=len(BOOKINGS)-1))
    else:
        flash('Van not available', 'danger')
        return redirect(url_for('list_vans'))

@app.route('/booking/<int:booking_id>')
def booking_confirmation(booking_id):
    if booking_id < len(BOOKINGS):
        booking = BOOKINGS[booking_id]
        van = next((v for v in VANS if v['id'] == booking['van_id']), None)
        return render_template('booking.html', booking=booking, van=van)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
