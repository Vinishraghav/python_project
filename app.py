import firebase_admin
from firebase_admin import credentials, auth
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
import os
import json
import stripe
import uuid
from dotenv import load_dotenv
from utils.email_utils import generate_otp, store_otp, verify_otp, send_otp_email

# Load environment variables
load_dotenv()

# Initialize Firebase
cred = credentials.Certificate('firebase_config.json')
firebase_admin.initialize_app(cred)

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

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
    {
        "id": 1,
        "name": "Premium Tour Van",
        "price": 120,
        "seats": 8,
        "available": True,
        "location": "New York City",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "blocked_dates": []
    },
    {
        "id": 2,
        "name": "Luxury Family Van",
        "price": 150,
        "seats": 12,
        "available": True,
        "location": "Los Angeles",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "blocked_dates": []
    },
    {
        "id": 3,
        "name": "Eco Adventure Van",
        "price": 90,
        "seats": 6,
        "available": True,
        "location": "Chicago",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "blocked_dates": []
    }
]

# Sample bookings with payment information
BOOKINGS = []

# Payment statuses
PAYMENT_STATUS = {
    'PENDING': 'pending',
    'PROCESSING': 'processing',
    'COMPLETED': 'completed',
    'FAILED': 'failed',
    'REFUNDED': 'refunded'
}

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

@app.route('/map')
def map_view():
    if 'user' not in session:
        return redirect(url_for('unified_login'))

    # Get filter parameters
    location = request.args.get('location', '')

    # Filter vans by location if specified
    filtered_vans = VANS
    if location:
        filtered_vans = [van for van in VANS if van['location'] == location]

    return render_template('map_view.html', vans=filtered_vans)

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

@app.route('/owner/dashboard')
def owner_dashboard():
    if 'user' not in session or session.get('role') != 'updator':
        flash("Access denied. You must be logged in as a van owner.", "danger")
        return redirect(url_for('unified_login'))

    # Get vans owned by this user
    owner_vans = [v for v in VANS]

    # Get bookings for these vans
    van_ids = [v['id'] for v in owner_vans]
    bookings = [b for b in BOOKINGS if b['van_id'] in van_ids]

    # Calculate statistics
    total_bookings = len(bookings)
    upcoming_bookings = [b for b in bookings if b['start_date'] > datetime.now()]
    active_bookings = [b for b in bookings if b['start_date'] <= datetime.now() <= b['end_date']]
    completed_bookings = [b for b in bookings if b['end_date'] < datetime.now()]

    # Calculate revenue
    total_revenue = sum(b['total_price'] for b in bookings)

    stats = {
        'total_bookings': total_bookings,
        'upcoming_bookings': len(upcoming_bookings),
        'active_bookings': len(active_bookings),
        'completed_bookings': len(completed_bookings),
        'total_revenue': total_revenue
    }

    # Get current month and year for calendar
    today = datetime.now()
    current_month = today.month
    current_year = today.year

    return render_template('owner_dashboard.html',
                          vans=owner_vans,
                          bookings=bookings,
                          stats=stats,
                          current_month=current_month,
                          current_year=current_year)

@app.route('/owner/calendar/<int:van_id>')
def owner_calendar(van_id):
    if 'user' not in session or session.get('role') != 'updator':
        flash("Access denied. You must be logged in as a van owner.", "danger")
        return redirect(url_for('unified_login'))

    van = next((v for v in VANS if v["id"] == van_id), None)
    if not van:
        flash("Van not found", "danger")
        return redirect(url_for('owner_dashboard'))

    # Get bookings for this van
    bookings = [b for b in BOOKINGS if b['van_id'] == van_id]

    # Get month and year from query parameters or use current date
    today = datetime.now()
    month = request.args.get('month', today.month, type=int)
    year = request.args.get('year', today.year, type=int)

    # Calculate previous and next month/year
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year

    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year

    # Get month name
    month_name = datetime(year, month, 1).strftime('%B')

    # Get blocked dates for this van (if any)
    blocked_dates = van.get('blocked_dates', [])

    # Generate calendar data
    import calendar
    cal = calendar.monthcalendar(year, month)

    # Convert calendar data to a more usable format
    calendar_weeks = []
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                # Day is outside the month
                week_data.append({'date': None})
            else:
                date = datetime(year, month, day)
                date_str = date.strftime('%Y-%m-%d')

                # Check if this date has a booking
                has_booking = any(
                    b['start_date'] <= date <= b['end_date'] for b in bookings
                )

                week_data.append({
                    'date': date,
                    'date_str': date_str,
                    'today': date.date() == today.date(),
                    'has_booking': has_booking
                })
        calendar_weeks.append(week_data)

    return render_template('owner_calendar.html',
                          van=van,
                          bookings=bookings,
                          month=month,
                          year=year,
                          month_name=month_name,
                          prev_month=prev_month,
                          prev_year=prev_year,
                          next_month=next_month,
                          next_year=next_year,
                          calendar_weeks=calendar_weeks,
                          blocked_dates=blocked_dates,
                          now=today)

@app.route('/owner/update_availability/<int:van_id>', methods=['POST'])
def update_availability(van_id):
    if 'user' not in session or session.get('role') != 'updator':
        flash("Access denied. You must be logged in as a van owner.", "danger")
        return redirect(url_for('unified_login'))

    van = next((v for v in VANS if v["id"] == van_id), None)
    if not van:
        flash("Van not found", "danger")
        return redirect(url_for('owner_dashboard'))

    # Get the date and availability status from the form
    date_str = request.form.get('date')
    action = request.form.get('action')  # 'block' or 'unblock'

    if not date_str or not action:
        flash("Invalid request", "danger")
        return redirect(url_for('owner_calendar', van_id=van_id))

    # Convert date string to datetime object
    date = datetime.strptime(date_str, '%Y-%m-%d')

    # Initialize blocked_dates if it doesn't exist
    if 'blocked_dates' not in van:
        van['blocked_dates'] = []

    # Update availability
    if action == 'block':
        if date_str not in van['blocked_dates']:
            van['blocked_dates'].append(date_str)
            flash(f"Date {date_str} has been blocked", "success")
    elif action == 'unblock':
        if date_str in van['blocked_dates']:
            van['blocked_dates'].remove(date_str)
            flash(f"Date {date_str} has been unblocked", "success")

    # Emit socket event for real-time updates
    van_data = {
        'id': van["id"],
        'name': van["name"],
        'blocked_dates': van.get('blocked_dates', [])
    }
    socketio.emit('availability_update', van_data)

    return redirect(url_for('owner_calendar', van_id=van_id))

@app.route('/owner/update_location/<int:van_id>', methods=['POST'])
def update_location(van_id):
    if 'user' not in session or session.get('role') != 'updator':
        return jsonify({"success": False, "error": "Access denied. You must be logged in as a van owner."})

    van = next((v for v in VANS if v["id"] == van_id), None)
    if not van:
        return jsonify({"success": False, "error": "Van not found"})

    # Get the new location from the request
    data = request.get_json()
    new_location = data.get('location')

    if not new_location:
        return jsonify({"success": False, "error": "Location is required"})

    # Update the van's location
    van['location'] = new_location
    van['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Emit socket event for real-time updates
    van_data = {
        'id': van["id"],
        'name': van["name"],
        'location': van["location"],
        'last_updated': van["last_updated"]
    }
    socketio.emit('van_update', van_data)

    return jsonify({"success": True, "message": f"Location updated to {new_location}"})

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

@app.route('/payment/<int:booking_id>')
def payment(booking_id):
    if 'user' not in session:
        return redirect(url_for('unified_login'))

    if booking_id < len(BOOKINGS):
        booking = BOOKINGS[booking_id]
        van = next((v for v in VANS if v['id'] == booking['van_id']), None)

        # Check if this booking belongs to the current user
        if booking['user'] != session['user']:
            flash('Access denied', 'danger')
            return redirect(url_for('home'))

        # Check if payment is already completed
        if booking.get('payment_status') == PAYMENT_STATUS['COMPLETED']:
            flash('Payment has already been completed for this booking', 'info')
            return redirect(url_for('booking_confirmation', booking_id=booking_id))

        # Get Stripe publishable key from environment
        stripe_publishable_key = os.environ.get('STRIPE_PUBLISHABLE_KEY')

        return render_template('payment.html', booking=booking, van=van, stripe_publishable_key=stripe_publishable_key)

    flash('Booking not found', 'danger')
    return redirect(url_for('home'))

@app.route('/create-payment-intent/<int:booking_id>', methods=['POST'])
def create_payment_intent(booking_id):
    if 'user' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    if booking_id < len(BOOKINGS):
        booking = BOOKINGS[booking_id]

        # Check if this booking belongs to the current user
        if booking['user'] != session['user']:
            return jsonify({"error": "Access denied"}), 403

        try:
            # Get billing information from request
            data = request.get_json()

            # Create a PaymentIntent with the order amount and currency
            intent = stripe.PaymentIntent.create(
                amount=int(booking['total_price'] * 100),  # Amount in cents
                currency='usd',
                metadata={
                    'booking_id': booking_id,
                    'user_email': session['user']
                }
            )

            # Update booking with payment intent ID
            booking['payment_id'] = intent.id
            booking['payment_status'] = PAYMENT_STATUS['PROCESSING']

            return jsonify({
                'clientSecret': intent.client_secret
            })

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Booking not found"}), 404

@app.route('/update-payment-status/<int:booking_id>', methods=['POST'])
def update_payment_status(booking_id):
    if 'user' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    if booking_id < len(BOOKINGS):
        booking = BOOKINGS[booking_id]

        # Check if this booking belongs to the current user
        if booking['user'] != session['user']:
            return jsonify({"error": "Access denied"}), 403

        try:
            data = request.get_json()
            payment_id = data.get('payment_id')
            payment_status = data.get('payment_status')

            # Update booking payment information
            booking['payment_id'] = payment_id
            booking['payment_status'] = PAYMENT_STATUS[payment_status.upper()]
            booking['payment_date'] = datetime.now()
            booking['payment_method'] = 'Credit Card'

            # Emit socket event for real-time updates
            payment_data = {
                'booking_id': booking_id,
                'payment_status': booking['payment_status'],
                'payment_date': booking['payment_date'].strftime('%Y-%m-%d %H:%M:%S')
            }
            socketio.emit('payment_update', payment_data)

            return jsonify({"success": True})

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Booking not found"}), 404

@app.route('/payment/receipt/<int:booking_id>')
def payment_receipt(booking_id):
    if 'user' not in session:
        return redirect(url_for('unified_login'))

    if booking_id < len(BOOKINGS):
        booking = BOOKINGS[booking_id]
        van = next((v for v in VANS if v['id'] == booking['van_id']), None)

        # Check if this booking belongs to the current user
        if booking['user'] != session['user']:
            flash('Access denied', 'danger')
            return redirect(url_for('home'))

        # Check if payment is completed
        if booking.get('payment_status') != PAYMENT_STATUS['COMPLETED']:
            flash('No payment receipt available for this booking', 'warning')
            return redirect(url_for('booking_confirmation', booking_id=booking_id))

        # Create payment object for the template
        payment = {
            'id': booking.get('payment_id', 'N/A'),
            'date': booking.get('payment_date', datetime.now()),
            'method': booking.get('payment_method', 'Credit Card'),
            'status': booking.get('payment_status'),
            'transaction_id': booking.get('payment_id', 'N/A'),
            'customer_name': session.get('user', '').split('@')[0],
            'customer_email': session.get('user', '')
        }

        return render_template('payment_receipt.html', booking=booking, van=van, payment=payment)

    flash('Booking not found', 'danger')
    return redirect(url_for('home'))

@app.route('/unified_login', methods=['GET', 'POST'])
def unified_login():
    if session.get('user'):
        if session.get('role') == 'updator':
            # Check if the request has a 'redirect' parameter
            redirect_to = request.args.get('redirect', '')
            if redirect_to == 'owner':
                return redirect(url_for('owner_dashboard'))
            else:
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

# Event for payment updates
@socketio.on('payment_update')
def handle_payment_update(data):
    # Broadcast the payment update to all connected clients
    emit('payment_update', data, broadcast=True)

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
        # Check if any of the dates are blocked
        blocked_dates = van.get('blocked_dates', [])

        # Generate a list of all dates in the booking range
        booking_dates = []
        current_date = start_date
        while current_date <= end_date:
            booking_dates.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)

        # Check if any booking date is in the blocked dates
        blocked = any(date in blocked_dates for date in booking_dates)

        if blocked:
            flash('Some of the selected dates are not available for this van', 'danger')
            return redirect(url_for('list_vans'))

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
            'status': 'confirmed',
            'payment_status': PAYMENT_STATUS['PENDING'],
            'payment_id': None,
            'payment_method': None,
            'payment_date': None
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
