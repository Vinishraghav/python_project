import firebase_admin
from firebase_admin import credentials, auth
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_socketio import SocketIO, emit
from datetime import datetime
import os
import json
from dotenv import load_dotenv
from utils.email_utils import generate_otp, store_otp, verify_otp, send_otp_email

# Load environment variables
load_dotenv()

# Initialize Firebase
cred = credentials.Certificate('firebase_config.json')
firebase_admin.initialize_app(cred)

# Initialize Flask
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_secret_key_here')
socketio = SocketIO(app, cors_allowed_origins="*")

# Sample user (for demo login)
USERS = [
    {"username": "vinish523@gmail.com", "password": "vinish123", "role": "user"},
    {"username": "vinish523@gmail.com", "password": "vinish123", "role": "updator"}
]

# Sample data
VANS = [
    {"id": 1, "name": "Premium Tour Van", "price": 120, "seats": 8, "available": True, "location": "New York City", "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")},
    {"id": 2, "name": "Luxury Family Van", "price": 150, "seats": 12, "available": True, "location": "Los Angeles", "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")},
    {"id": 3, "name": "Eco Adventure Van", "price": 90, "seats": 6, "available": True, "location": "Chicago", "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")}
]

BOOKINGS = []

@app.route('/')
def welcome():
    if session.get('user'):
        if session.get('role') == 'updator':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('home'))
    return render_template('role_selection.html')

@app.route('/role_selection')
def role_selection():
    if session.get('user'):
        if session.get('role') == 'updator':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('home'))
    return render_template('role_selection.html')

# Removed traditional login route - using Firebase authentication only

# Firebase authentication route

@app.route('/verify', methods=['POST'])
def verify():
    try:
        id_token = request.json.get('idToken')
        role = request.json.get('role')

        if not role:
            return jsonify({"success": False, "error": "Role is required"})

        decoded_token = auth.verify_id_token(id_token)
        email = decoded_token['email']
        uid = decoded_token['uid']

        # Store user information in session
        session['user'] = email
        session['uid'] = uid
        session['role'] = role

        # Determine redirect based on role
        redirect_url = '/home'
        if role == 'updator':
            redirect_url = '/admin'

        return jsonify({
            "success": True,
            "redirect": redirect_url
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/register_role', methods=['POST'])
def register_role():
    try:
        id_token = request.json.get('idToken')
        role = request.json.get('role')

        if not role:
            return jsonify({"success": False, "error": "Role is required"})

        decoded_token = auth.verify_id_token(id_token)
        email = decoded_token['email']
        uid = decoded_token['uid']

        # In a real application, you would store this in a database
        # For now, we'll just return success
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/send_otp', methods=['POST'])
def send_otp():
    try:
        email = request.json.get('email')
        role = request.json.get('role')
        id_token = request.json.get('idToken')

        if not email or not role or not id_token:
            return jsonify({"success": False, "error": "Email, role, and ID token are required"})

        # Verify Firebase token
        try:
            decoded_token = auth.verify_id_token(id_token)
            if decoded_token['email'] != email:
                return jsonify({"success": False, "error": "Email verification failed"})
        except Exception as e:
            return jsonify({"success": False, "error": f"Token verification failed: {str(e)}"})

        # Generate OTP
        otp = generate_otp()

        # Store OTP with expiration
        store_otp(email, otp)

        # Send OTP via email
        if send_otp_email(email, otp):
            # For demonstration purposes, we're returning the OTP in the response
            # In a real application, you would never do this!
            return jsonify({"success": True, "otp": otp})
        else:
            return jsonify({"success": False, "error": "Failed to send verification email"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/verify_otp', methods=['POST'])
def verify_otp_route():
    try:
        email = request.json.get('email')
        otp = request.json.get('otp')
        role = request.json.get('role')
        id_token = request.json.get('idToken')

        if not email or not otp or not role or not id_token:
            return jsonify({"success": False, "error": "Email, OTP, role, and ID token are required"})

        # Verify Firebase token
        try:
            decoded_token = auth.verify_id_token(id_token)
            if decoded_token['email'] != email:
                return jsonify({"success": False, "error": "Email verification failed"})
        except Exception as e:
            return jsonify({"success": False, "error": f"Token verification failed: {str(e)}"})

        # Verify OTP
        if verify_otp(email, otp):
            # Store user information in session
            session['user'] = email
            session['uid'] = decoded_token['uid']
            session['role'] = role

            # Determine redirect based on role
            redirect_url = '/home'
            if role == 'updator':
                redirect_url = '/admin'

            return jsonify({
                "success": True,
                "redirect": redirect_url
            })
        else:
            return jsonify({"success": False, "error": "Invalid or expired verification code"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/resend_otp', methods=['POST'])
def resend_otp():
    try:
        email = request.json.get('email')
        role = request.json.get('role')

        if not email or not role:
            return jsonify({"success": False, "error": "Email and role are required"})

        # Generate new OTP
        otp = generate_otp()

        # Store OTP with expiration
        store_otp(email, otp)

        # Send OTP via email
        if send_otp_email(email, otp):
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Failed to send verification email"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/verify_otp')
def verify_otp_page():
    email = request.args.get('email')
    role = request.args.get('role')
    id_token = request.args.get('token')

    if not email or not role or not id_token:
        flash("Missing required parameters", "danger")
        return redirect(url_for('signup_page'))

    return render_template('verify_otp.html', email=email, role=role, id_token=id_token)


# The admin route should be defined once.
@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'updator':
        flash("Access denied", "danger")
        return redirect(url_for('unified_login'))
    return render_template('admin.html', vans=VANS, BOOKINGS=BOOKINGS)

@app.route('/signup_page')
def signup_page():
    if session.get('user'):
        if session.get('role') == 'updator':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('home'))

    # Get the role from the query parameter
    role = request.args.get('role', '')
    return render_template('signup.html', role=role)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        role = request.form.get('role', '')

        # Check if user already exists
        user_exists = any(u['username'] == username and u['role'] == role for u in USERS)

        if user_exists:
            flash('User already exists with this email and role', 'danger')
            return redirect(url_for('signup_page'))

        # Add new user
        USERS.append({
            'username': username,
            'password': password,
            'role': role
        })

        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('unified_login'))

    return redirect(url_for('signup_page'))

@app.route('/login_page')
def login_page():
    return render_template('login.html')

@app.route('/test', methods=['GET'])
def test_login_page():
    return render_template('test_login.html')

@app.route('/test_login', methods=['POST'])
def test_login():
    print("Test login attempt received")
    print(f"Form data: {request.form}")

    username = request.form.get('username', '')
    password = request.form.get('password', '')
    role = request.form.get('role', '')

    print(f"Login attempt: username={username}, role={role}")

    # Check if credentials match
    user = next((u for u in USERS if u['username'] == username and u['password'] == password and u['role'] == role), None)

    if user:
        print(f"User found: {user}")
        session['user'] = username
        session['role'] = role
        flash(f'Logged in as {role}', 'success')

        # Redirect based on role
        if role == 'user':
            print("Redirecting to home")
            return redirect(url_for('home'))  # Main booking page
        elif role == 'updator':
            print("Redirecting to admin dashboard")
            return redirect(url_for('admin_dashboard'))  # Admin view
    else:
        print("Invalid credentials")
        flash('Invalid credentials or role', 'danger')
        return redirect(url_for('test_login_page'))

    return redirect(url_for('welcome'))


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('welcome'))

@app.route('/home')
def home():
    if 'user' not in session:
        return redirect(url_for('unified_login'))
    return render_template('index.html')

@app.route('/vans')
def list_vans():
    if 'user' not in session:
        return redirect(url_for('unified_login'))

    # Get filter parameters
    location = request.args.get('location', '')

    # Filter vans by location if specified
    filtered_vans = VANS
    if location:
        filtered_vans = [van for van in VANS if van['location'] == location]

    return render_template('vans.html', vans=filtered_vans)

@app.route('/admin/add', methods=['GET', 'POST'])
def add_van():
    if session.get('role') != 'updator':
        flash("Access denied", "danger")
        return redirect(url_for('unified_login'))
    if request.method == 'POST':
        new_van = {
            "id": max([v["id"] for v in VANS]) + 1 if VANS else 1,
            "name": request.form['name'],
            "price": int(request.form['price']),
            "seats": int(request.form['seats']),
            "available": True,
            "location": request.form['location'],
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        VANS.append(new_van)

        # Emit socket event for real-time updates
        van_data = {
            'id': new_van["id"],
            'name': new_van["name"],
            'location': new_van["location"],
            'last_updated': new_van["last_updated"]
        }
        socketio.emit('van_update', van_data)

        flash("Van added successfully!", "success")
        return redirect(url_for('admin_dashboard'))
    return render_template('add_van.html')

@app.route('/admin/edit/<int:van_id>', methods=['GET', 'POST'])
def edit_van(van_id):
    if session.get('role') != 'updator':
        flash("Access denied", "danger")
        return redirect(url_for('unified_login'))
    van = next((v for v in VANS if v["id"] == van_id), None)
    if not van:
        flash("Van not found", "danger")
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        van["name"] = request.form['name']
        van["price"] = int(request.form['price'])
        van["seats"] = int(request.form['seats'])
        van["location"] = request.form['location']
        van["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Emit socket event for real-time updates
        van_data = {
            'id': van["id"],
            'name': van["name"],
            'location': van["location"],
            'last_updated': van["last_updated"]
        }
        socketio.emit('van_update', van_data)

        flash("Van updated successfully!", "success")
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_van.html', van=van)

@app.route('/admin/delete/<int:van_id>', methods=['POST'])
def delete_van(van_id):
    if session.get('role') != 'updator':
        flash("Access denied", "danger")
        return redirect(url_for('unified_login'))
    global VANS
    VANS = [v for v in VANS if v["id"] != van_id]
    flash("Van deleted successfully!", "success")
    return redirect(url_for('admin_dashboard'))

# Original book route replaced by the Socket.IO version below

@app.route('/booking/<int:booking_id>')
def booking_confirmation(booking_id):
    if 'user' not in session:
        return redirect(url_for('unified_login'))

    if booking_id < len(BOOKINGS):
        booking = BOOKINGS[booking_id]
        van = next((v for v in VANS if v['id'] == booking['van_id']), None)
        return render_template('booking.html', booking=booking, van=van)
    return redirect(url_for('home'))

@app.route('/unified_login', methods=['GET', 'POST'])
def unified_login():
    if session.get('user'):
        if session.get('role') == 'updator':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('home'))
    return render_template('unified_login.html')

@app.route('/debug')
def debug_session():
    return f"""
    <h1>Session Debug</h1>
    <p>Session: {session}</p>
    <p>User: {session.get('user', 'Not logged in')}</p>
    <p>Role: {session.get('role', 'No role')}</p>
    <p><a href="/">Home</a></p>
    <p><a href="/test">Test Login</a></p>
    <p><a href="/logout">Logout</a></p>
    """

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

# Event for booking updates
@socketio.on('booking_update')
def handle_booking_update(data):
    # Broadcast the booking update to all connected clients
    emit('booking_update', data, broadcast=True)

# Event for van availability updates
@socketio.on('van_update')
def handle_van_update(data):
    # Broadcast the van update to all connected clients
    emit('van_update', data, broadcast=True)

# Update the book route to emit a socket event
@app.route('/book', methods=['POST'])
def book():
    if 'user' not in session:
        return redirect(url_for('unified_login'))

    van_id = int(request.form['van_id'])
    start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
    end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
    passengers = int(request.form['passengers'])

    # Get total price from form if provided, otherwise calculate it
    total_price = request.form.get('total_price')
    if total_price:
        total_price = int(total_price)

    van = next((v for v in VANS if v['id'] == van_id), None)

    if van:
        # Calculate total price if not provided
        if not total_price:
            days = (end_date - start_date).days
            if days < 1:
                days = 1
            total_price = van['price'] * days

        # Create booking with ID
        booking_id = len(BOOKINGS)
        booking = {
            'id': booking_id,
            'van_id': van_id,
            'user': session['user'],
            'start_date': start_date,
            'end_date': end_date,
            'passengers': passengers,
            'total_price': total_price,
            'booking_date': datetime.now(),
            'status': 'confirmed'
        }
        BOOKINGS.append(booking)

        # Emit socket event for real-time updates
        booking_data = {
            'id': booking_id,
            'van_id': van_id,
            'van_name': van['name'],
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'total_price': total_price,
            'user': session['user']
        }
        socketio.emit('booking_update', booking_data)

        flash('Booking confirmed!', 'success')
        return redirect(url_for('booking_confirmation', booking_id=booking_id))
    else:
        flash('Van not available', 'danger')
        return redirect(url_for('list_vans'))

if __name__ == '__main__':
    socketio.run(app, debug=True)
