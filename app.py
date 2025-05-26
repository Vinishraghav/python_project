import firebase_admin
from firebase_admin import credentials, auth
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
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
    {"username": "vinish523@gmail.com", "password": "vinish123", "role": "updater"}
]

# Sample data with enhanced van information
VANS = [
    {
        "id": 1,
        "name": "Premium Tour Van",
        "price": 120,
        "seats": 8,
        "available": True,
        "location": "New York City",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "blocked_dates": [],
        "description": "Perfect for weekend getaways and outdoor adventures.",
        "image": "/static/img/van1.jpg",
        "amenities": ["WiFi", "Kitchen", "Bed", "Solar Power", "Shower"],
        "fuel_type": "Gasoline",
        "transmission": "Manual",
        "year": 2020,
        "mileage": "25 MPG",
        "features": ["GPS Navigation", "Backup Camera", "Air Conditioning", "Heating"],
        "category": "Adventure",
        "rating": 4.5,
        "total_reviews": 23
    },
    {
        "id": 2,
        "name": "Luxury Family Van",
        "price": 150,
        "seats": 12,
        "available": True,
        "location": "Los Angeles",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "blocked_dates": [],
        "description": "Spacious van perfect for family trips.",
        "image": "/static/img/van2.jpg",
        "amenities": ["WiFi", "Full Kitchen", "Multiple Beds", "Shower", "Toilet", "TV"],
        "fuel_type": "Diesel",
        "transmission": "Automatic",
        "year": 2021,
        "mileage": "30 MPG",
        "features": ["GPS Navigation", "Backup Camera", "Air Conditioning", "Heating", "Entertainment System"],
        "category": "Family",
        "rating": 4.8,
        "total_reviews": 35
    },
    {
        "id": 3,
        "name": "Eco Adventure Van",
        "price": 90,
        "seats": 6,
        "available": True,
        "location": "Chicago",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "blocked_dates": [],
        "description": "Compact and efficient for city exploration.",
        "image": "/static/img/van3.jpg",
        "amenities": ["WiFi", "Kitchenette", "Bed"],
        "fuel_type": "Electric",
        "transmission": "Automatic",
        "year": 2022,
        "mileage": "100 MPGe",
        "features": ["GPS Navigation", "USB Charging", "Air Conditioning"],
        "category": "Urban",
        "rating": 4.2,
        "total_reviews": 18
    },
    {
        "id": 4,
        "name": "Luxury Nomad",
        "price": 300,
        "seats": 4,
        "available": True,
        "location": "Seattle",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "blocked_dates": ["2025-01-15", "2025-01-16"],
        "description": "Premium van with luxury amenities for the discerning traveler.",
        "image": "/static/img/van4.jpg",
        "amenities": ["WiFi", "Gourmet Kitchen", "Queen Bed", "Shower", "Toilet", "TV", "Sound System"],
        "fuel_type": "Hybrid",
        "transmission": "Automatic",
        "year": 2023,
        "mileage": "35 MPG",
        "features": ["GPS Navigation", "Backup Camera", "Air Conditioning", "Heating", "Entertainment System", "Leather Seats"],
        "category": "Luxury",
        "rating": 4.9,
        "total_reviews": 12
    },
    {
        "id": 5,
        "name": "Budget Wanderer",
        "price": 80,
        "seats": 2,
        "available": True,
        "location": "Portland",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "blocked_dates": [],
        "description": "Affordable option for budget-conscious travelers.",
        "image": "/static/img/van5.jpg",
        "amenities": ["Basic Kitchen", "Bed"],
        "fuel_type": "Gasoline",
        "transmission": "Manual",
        "year": 2018,
        "mileage": "22 MPG",
        "features": ["Basic Radio", "Manual Windows"],
        "category": "Budget",
        "rating": 3.8,
        "total_reviews": 8
    }
]

# Sample saved searches
SAVED_SEARCHES = []

# Sample favorite vans
FAVORITE_VANS = []

# Sample chat conversations
CHAT_CONVERSATIONS = []

# Sample chat messages
CHAT_MESSAGES = []

# Sample support tickets
SUPPORT_TICKETS = []

# Sample bookings with payment information
BOOKINGS = []

# Sample reviews
REVIEWS = [
    {
        'id': 0,
        'booking_id': 0,
        'van_id': 0,
        'user': 'user@example.com',
        'user_name': 'John Doe',
        'rating': 5,
        'title': 'Amazing van experience!',
        'content': 'The van was perfect for our family trip. Clean, comfortable, and well-equipped. Highly recommend!',
        'cleanliness': 5,
        'comfort': 5,
        'value': 4,
        'service': 5,
        'recommend': True,
        'date': datetime.now() - timedelta(days=5),
        'status': REVIEW_STATUS['APPROVED'],
        'photos': [],
        'owner_response': 'Thank you for the wonderful review! We\'re glad you enjoyed your trip.',
        'response_date': datetime.now() - timedelta(days=3)
    },
    {
        'id': 1,
        'booking_id': 1,
        'van_id': 0,
        'user': 'user2@example.com',
        'user_name': 'Jane Smith',
        'rating': 4,
        'title': 'Great value for money',
        'content': 'Good van with all necessary amenities. The pickup was smooth and the van was clean.',
        'cleanliness': 4,
        'comfort': 4,
        'value': 5,
        'service': 4,
        'recommend': True,
        'date': datetime.now() - timedelta(days=10),
        'status': REVIEW_STATUS['APPROVED'],
        'photos': [],
        'owner_response': None,
        'response_date': None
    },
    {
        'id': 2,
        'booking_id': 2,
        'van_id': 1,
        'user': 'user3@example.com',
        'user_name': 'Mike Johnson',
        'rating': 5,
        'title': 'Perfect for our adventure!',
        'content': 'This van was exactly what we needed for our camping trip. Spacious and reliable.',
        'cleanliness': 5,
        'comfort': 5,
        'value': 5,
        'service': 5,
        'recommend': True,
        'date': datetime.now() - timedelta(days=15),
        'status': REVIEW_STATUS['APPROVED'],
        'photos': [],
        'owner_response': 'So happy you had a great adventure! Come back anytime.',
        'response_date': datetime.now() - timedelta(days=12)
    },
    {
        'id': 3,
        'booking_id': 3,
        'van_id': 2,
        'user': 'user4@example.com',
        'user_name': 'Sarah Wilson',
        'rating': 3,
        'title': 'Decent van, some issues',
        'content': 'The van was okay but had some minor issues with the air conditioning. Overall acceptable.',
        'cleanliness': 3,
        'comfort': 3,
        'value': 3,
        'service': 4,
        'recommend': False,
        'date': datetime.now() - timedelta(days=20),
        'status': REVIEW_STATUS['APPROVED'],
        'photos': [],
        'owner_response': 'Thank you for the feedback. We\'ve fixed the AC issue.',
        'response_date': datetime.now() - timedelta(days=18)
    }
]

# Sample notifications
NOTIFICATIONS = []

# Payment statuses
PAYMENT_STATUS = {
    'PENDING': 'pending',
    'PROCESSING': 'processing',
    'COMPLETED': 'completed',
    'FAILED': 'failed',
    'REFUNDED': 'refunded'
}

# Review statuses
REVIEW_STATUS = {
    'PENDING': 'pending',
    'APPROVED': 'approved',
    'REJECTED': 'rejected'
}

# Notification types
NOTIFICATION_TYPE = {
    'BOOKING_CONFIRMED': 'booking_confirmed',
    'BOOKING_CANCELLED': 'booking_cancelled',
    'PAYMENT_RECEIVED': 'payment_received',
    'PAYMENT_FAILED': 'payment_failed',
    'REVIEW_RECEIVED': 'review_received',
    'REVIEW_RESPONSE': 'review_response',
    'TRIP_REMINDER': 'trip_reminder',
    'SYSTEM': 'system'
}

# Notification status
NOTIFICATION_STATUS = {
    'UNREAD': 'unread',
    'READ': 'read'
}

# Chat conversation status
CHAT_STATUS = {
    'ACTIVE': 'active',
    'CLOSED': 'closed',
    'WAITING': 'waiting'
}

# Support ticket status
TICKET_STATUS = {
    'OPEN': 'open',
    'IN_PROGRESS': 'in_progress',
    'RESOLVED': 'resolved',
    'CLOSED': 'closed'
}

# Support ticket priority
TICKET_PRIORITY = {
    'LOW': 'low',
    'MEDIUM': 'medium',
    'HIGH': 'high',
    'URGENT': 'urgent'
}

# Message types
MESSAGE_TYPE = {
    'USER': 'user',
    'SUPPORT': 'support',
    'SYSTEM': 'system'
}

@app.route('/')
def welcome():
    if session.get('user'):
        if session.get('role') == 'updater':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('home'))
    return render_template('role_selection.html')

@app.route('/role_selection')
def role_selection():
    if session.get('user'):
        if session.get('role') == 'updater':
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
        if role == 'updater':
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
            if role == 'updater':
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
    if session.get('role') != 'updater':
        flash("Access denied", "danger")
        return redirect(url_for('unified_login'))
    return render_template('admin.html', vans=VANS, BOOKINGS=BOOKINGS)

@app.route('/signup_page')
def signup_page():
    if session.get('user'):
        if session.get('role') == 'updater':
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
        elif role == 'updater':
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

    # Get search parameters
    location = request.args.get('location', '')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    passengers = request.args.get('passengers', 1, type=int)

    # If no trip details are provided, redirect to home page
    if not start_date or not end_date:
        flash('Please select your trip dates first to see available vans.', 'info')
        return redirect(url_for('home'))

    # Filter vans based on criteria
    filtered_vans = []
    for van in VANS:
        # Filter by location if specified
        if location and location.lower() not in van['location'].lower():
            continue

        # Filter by passenger capacity
        if van['seats'] < passengers:
            continue

        # Check availability for the selected dates
        if start_date and end_date:
            # Convert dates to check against blocked dates
            blocked_dates = van.get('blocked_dates', [])

            # Generate a list of all dates in the booking range
            booking_dates = []
            current_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')

            while current_date <= end_date_obj:
                booking_dates.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)

            # Check if any booking date is in the blocked dates
            blocked = any(date in blocked_dates for date in booking_dates)

            if blocked:
                continue

        # Add rating information to van
        van_reviews = [r for r in REVIEWS if r['van_id'] == van['id'] and r['status'] == REVIEW_STATUS['APPROVED']]
        if van_reviews:
            avg_rating = sum(r['rating'] for r in van_reviews) / len(van_reviews)
            van['avg_rating'] = round(avg_rating, 1)
            van['review_count'] = len(van_reviews)
        else:
            van['avg_rating'] = 0
            van['review_count'] = 0

        filtered_vans.append(van)

    # Calculate trip duration for price calculation
    trip_days = 1
    if start_date and end_date:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        trip_days = (end_dt - start_dt).days
        if trip_days < 1:
            trip_days = 1

    return render_template('vans.html', vans=filtered_vans, trip_days=trip_days)

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
    if session.get('role') != 'updater':
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
    if session.get('role') != 'updater':
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
    if session.get('role') != 'updater':
        flash("Access denied", "danger")
        return redirect(url_for('unified_login'))
    global VANS
    VANS = [v for v in VANS if v["id"] != van_id]
    flash("Van deleted successfully!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/owner/dashboard')
def owner_dashboard():
    if 'user' not in session or session.get('role') != 'updater':
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
    if 'user' not in session or session.get('role') != 'updater':
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
    if 'user' not in session or session.get('role') != 'updater':
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
    if 'user' not in session or session.get('role') != 'updater':
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

            # Get the van details
            van = next((v for v in VANS if v['id'] == booking['van_id']), None)

            # Create notification for payment completion
            if payment_status.upper() == 'COMPLETED':
                # Notification for the user
                create_notification(
                    user_email=session['user'],
                    notification_type=NOTIFICATION_TYPE['PAYMENT_RECEIVED'],
                    title='Payment Confirmed',
                    message=f'Your payment of ${booking["total_price"]} for booking #{booking_id} has been received.',
                    related_id=booking_id,
                    related_type='payment'
                )

                # Notification for the van owner
                if van:
                    # In a real app, you would get the owner's email from the van object
                    owner_email = "admin@example.com"  # This would be van['owner_email'] in a real app
                    create_notification(
                        user_email=owner_email,
                        notification_type=NOTIFICATION_TYPE['PAYMENT_RECEIVED'],
                        title='Payment Received',
                        message=f'Payment of ${booking["total_price"]} has been received for booking #{booking_id}.',
                        related_id=booking_id,
                        related_type='payment'
                    )
            elif payment_status.upper() == 'FAILED':
                # Notification for payment failure
                create_notification(
                    user_email=session['user'],
                    notification_type=NOTIFICATION_TYPE['PAYMENT_FAILED'],
                    title='Payment Failed',
                    message=f'Your payment for booking #{booking_id} has failed. Please try again or contact support.',
                    related_id=booking_id,
                    related_type='payment'
                )

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

@app.route('/my-bookings')
def my_bookings():
    if 'user' not in session:
        return redirect(url_for('unified_login'))

    # Get all bookings for the current user
    user_bookings = [b for b in BOOKINGS if b['user'] == session['user']]

    # Create a dictionary of vans for easy lookup
    vans_dict = {van['id']: van for van in VANS}

    # Get the current date for determining booking status
    current_date = datetime.now()

    # Get list of bookings that have been reviewed
    reviewed_bookings = [review['booking_id'] for review in REVIEWS if review['user'] == session['user']]

    return render_template('my_bookings.html',
                          bookings=user_bookings,
                          vans_dict=vans_dict,
                          current_date=current_date,
                          reviewed_bookings=reviewed_bookings)

@app.route('/submit-review/<int:booking_id>', methods=['GET', 'POST'])
def submit_review(booking_id):
    if 'user' not in session:
        return redirect(url_for('unified_login'))

    if booking_id < len(BOOKINGS):
        booking = BOOKINGS[booking_id]
        van = next((v for v in VANS if v['id'] == booking['van_id']), None)

        # Check if this booking belongs to the current user
        if booking['user'] != session['user']:
            flash('Access denied', 'danger')
            return redirect(url_for('home'))

        # Check if booking is completed
        if booking['end_date'] > datetime.now():
            flash('You can only review completed bookings', 'warning')
            return redirect(url_for('my_bookings'))

        # Check if user has already reviewed this booking
        existing_review = next((r for r in REVIEWS if r['booking_id'] == booking_id and r['user'] == session['user']), None)
        if existing_review:
            flash('You have already reviewed this booking', 'info')
            return redirect(url_for('view_review', review_id=existing_review['id']))

        if request.method == 'POST':
            # Get form data
            rating = int(request.form.get('rating'))
            title = request.form.get('title')
            content = request.form.get('content')
            cleanliness = int(request.form.get('cleanliness', 0))
            comfort = int(request.form.get('comfort', 0))
            value = int(request.form.get('value', 0))
            service = int(request.form.get('service', 0))
            recommend = request.form.get('recommend') == 'yes'

            # Create new review
            review_id = len(REVIEWS)
            review = {
                'id': review_id,
                'booking_id': booking_id,
                'van_id': booking['van_id'],
                'user': session['user'],
                'user_name': session['user'].split('@')[0],
                'rating': rating,
                'title': title,
                'content': content,
                'cleanliness': cleanliness,
                'comfort': comfort,
                'value': value,
                'service': service,
                'recommend': recommend,
                'date': datetime.now(),
                'status': REVIEW_STATUS['PENDING'],
                'photos': [],
                'owner_response': None,
                'response_date': None
            }

            REVIEWS.append(review)

            # Emit socket event for real-time updates
            review_data = {
                'id': review_id,
                'van_id': booking['van_id'],
                'van_name': van['name'],
                'rating': rating,
                'user': session['user']
            }
            socketio.emit('review_update', review_data)

            # Create notification for the user
            create_notification(
                user_email=session['user'],
                notification_type=NOTIFICATION_TYPE['REVIEW_RECEIVED'],
                title='Review Submitted',
                message=f'Your review for {van["name"]} has been submitted successfully.',
                related_id=review_id,
                related_type='review'
            )

            # Create notification for the van owner
            # In a real app, you would get the owner's email from the van object
            owner_email = "admin@example.com"  # This would be van['owner_email'] in a real app
            create_notification(
                user_email=owner_email,
                notification_type=NOTIFICATION_TYPE['REVIEW_RECEIVED'],
                title='New Review Received',
                message=f'You have received a new {rating}-star review for {van["name"]}.',
                related_id=review_id,
                related_type='review'
            )

            flash('Your review has been submitted successfully', 'success')
            return redirect(url_for('view_review', review_id=review_id))

        return render_template('submit_review.html', booking=booking, van=van)

    flash('Booking not found', 'danger')
    return redirect(url_for('my_bookings'))

@app.route('/view-review/<int:review_id>')
def view_review(review_id):
    if 'user' not in session:
        return redirect(url_for('unified_login'))

    if review_id < len(REVIEWS):
        review = REVIEWS[review_id]

        # Check if this review belongs to the current user or if the user is the van owner
        is_owner = session.get('role') == 'updater'
        if review['user'] != session['user'] and not is_owner:
            flash('Access denied', 'danger')
            return redirect(url_for('home'))

        booking = next((b for b in BOOKINGS if b['id'] == review['booking_id']), None)
        van = next((v for v in VANS if v['id'] == review['van_id']), None)

        return render_template('view_review.html', review=review, booking=booking, van=van)

    flash('Review not found', 'danger')
    return redirect(url_for('my_bookings'))

@app.route('/van-reviews/<int:van_id>')
def van_reviews(van_id):
    if 'user' not in session:
        return redirect(url_for('unified_login'))

    van = next((v for v in VANS if v['id'] == van_id), None)
    if not van:
        flash('Van not found', 'danger')
        return redirect(url_for('list_vans'))

    # Get all approved reviews for this van
    van_reviews = [r for r in REVIEWS if r['van_id'] == van_id and r['status'] == REVIEW_STATUS['APPROVED']]

    # Calculate average rating
    if van_reviews:
        average_rating = sum(r['rating'] for r in van_reviews) / len(van_reviews)
    else:
        average_rating = 0

    # Calculate rating counts
    rating_counts = {}
    for i in range(1, 6):
        rating_counts[i] = len([r for r in van_reviews if r['rating'] == i])

    # Calculate category ratings
    category_ratings = {
        'cleanliness': sum(r['cleanliness'] for r in van_reviews) / len(van_reviews) if van_reviews else 0,
        'comfort': sum(r['comfort'] for r in van_reviews) / len(van_reviews) if van_reviews else 0,
        'value': sum(r['value'] for r in van_reviews) / len(van_reviews) if van_reviews else 0,
        'service': sum(r['service'] for r in van_reviews) / len(van_reviews) if van_reviews else 0
    }

    # Calculate recommendation percentage
    if van_reviews:
        recommend_count = len([r for r in van_reviews if r['recommend']])
        recommend_percentage = int((recommend_count / len(van_reviews)) * 100)
    else:
        recommend_percentage = 0

    return render_template('reviews.html',
                          van=van,
                          reviews=van_reviews,
                          average_rating=average_rating,
                          rating_counts=rating_counts,
                          category_ratings=category_ratings,
                          recommend_percentage=recommend_percentage)

@app.route('/owner/reviews')
def owner_reviews():
    if 'user' not in session or session.get('role') != 'updater':
        flash("Access denied. You must be logged in as a van owner.", "danger")
        return redirect(url_for('unified_login'))

    # Get all vans owned by this user
    owner_vans = [v for v in VANS]

    # Get all reviews for these vans
    van_ids = [v['id'] for v in owner_vans]
    owner_reviews = [r for r in REVIEWS if r['van_id'] in van_ids]

    # Calculate review statistics
    stats = {
        'total_reviews': len(owner_reviews),
        'average_rating': sum(r['rating'] for r in owner_reviews) / len(owner_reviews) if owner_reviews else 0,
        'recommend_percentage': int((len([r for r in owner_reviews if r['recommend']]) / len(owner_reviews)) * 100) if owner_reviews else 0,
        'response_rate': int((len([r for r in owner_reviews if r['owner_response']]) / len(owner_reviews)) * 100) if owner_reviews else 0
    }

    return render_template('owner_reviews.html', reviews=owner_reviews, stats=stats)

@app.route('/submit-response', methods=['POST'])
def submit_response():
    if 'user' not in session or session.get('role') != 'updater':
        flash("Access denied. You must be logged in as a van owner.", "danger")
        return redirect(url_for('unified_login'))

    review_id = int(request.form.get('review_id'))
    response = request.form.get('response')

    if review_id < len(REVIEWS):
        review = REVIEWS[review_id]

        # Get the van to check ownership
        van = next((v for v in VANS if v['id'] == review['van_id']), None)
        if not van:
            flash('Van not found', 'danger')
            return redirect(url_for('owner_reviews'))

        # Update the review with the owner's response
        review['owner_response'] = response
        review['response_date'] = datetime.now()

        # Emit socket event for real-time updates
        response_data = {
            'review_id': review_id,
            'van_id': review['van_id'],
            'response': response
        }
        socketio.emit('review_response_update', response_data)

        # Create notification for the review author
        create_notification(
            user_email=review['user'],
            notification_type=NOTIFICATION_TYPE['REVIEW_RESPONSE'],
            title='Response to Your Review',
            message=f'The owner has responded to your review for {van["name"]}.',
            related_id=review_id,
            related_type='review_response'
        )

        flash('Your response has been submitted successfully', 'success')
        return redirect(url_for('owner_reviews'))

    flash('Review not found', 'danger')
    return redirect(url_for('owner_reviews'))

@app.route('/cancel-booking', methods=['POST'])
def cancel_booking():
    if 'user' not in session:
        return redirect(url_for('unified_login'))

    booking_id = int(request.form.get('booking_id'))
    reason = request.form.get('reason')
    other_reason = request.form.get('other_reason')

    if booking_id < len(BOOKINGS):
        booking = BOOKINGS[booking_id]

        # Check if this booking belongs to the current user
        if booking['user'] != session['user']:
            flash('Access denied', 'danger')
            return redirect(url_for('home'))

        # Check if booking is upcoming
        if booking['start_date'] < datetime.now():
            flash('You can only cancel upcoming bookings', 'warning')
            return redirect(url_for('my_bookings'))

        # Get van details for notification
        van = next((v for v in VANS if v['id'] == booking['van_id']), None)

        # Update booking status
        booking['status'] = 'cancelled'
        booking['cancel_reason'] = other_reason if reason == 'other' else reason
        booking['cancel_date'] = datetime.now()

        # Create notification for the user
        create_notification(
            user_email=session['user'],
            notification_type=NOTIFICATION_TYPE['BOOKING_CANCELLED'],
            title='Booking Cancelled',
            message=f'Your booking for {van["name"] if van else "the van"} has been cancelled.',
            related_id=booking_id,
            related_type='booking'
        )

        # Create notification for the van owner
        if van:
            owner_email = "admin@example.com"  # This would be van['owner_email'] in a real app
            create_notification(
                user_email=owner_email,
                notification_type=NOTIFICATION_TYPE['BOOKING_CANCELLED'],
                title='Booking Cancelled',
                message=f'A booking for {van["name"]} has been cancelled by the customer.',
                related_id=booking_id,
                related_type='booking'
            )

        # Emit socket event for real-time updates
        cancel_data = {
            'booking_id': booking_id,
            'van_id': booking['van_id'],
            'status': 'cancelled'
        }
        socketio.emit('booking_update', cancel_data)

        flash('Your booking has been cancelled successfully', 'success')
        return redirect(url_for('my_bookings'))

    flash('Booking not found', 'danger')
    return redirect(url_for('my_bookings'))

@app.route('/notifications')
def notifications():
    if 'user' not in session:
        return redirect(url_for('unified_login'))

    # Get all notifications for the current user
    user_notifications = [n for n in NOTIFICATIONS if n['user'] == session['user']]

    # Sort by creation date (newest first)
    user_notifications.sort(key=lambda x: x['created_at'], reverse=True)

    # Count unread notifications
    unread_count = len([n for n in user_notifications if n['status'] == NOTIFICATION_STATUS['UNREAD']])

    return render_template('notifications.html',
                          notifications=user_notifications,
                          unread_count=unread_count)

@app.route('/notifications/mark-read/<int:notification_id>', methods=['POST'])
def mark_notification_read(notification_id):
    if 'user' not in session:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    if notification_id < len(NOTIFICATIONS):
        notification = NOTIFICATIONS[notification_id]

        # Check if this notification belongs to the current user
        if notification['user'] != session['user']:
            return jsonify({"success": False, "error": "Access denied"}), 403

        # Mark as read
        notification['status'] = NOTIFICATION_STATUS['READ']
        notification['read_at'] = datetime.now()

        return jsonify({"success": True})

    return jsonify({"success": False, "error": "Notification not found"}), 404

@app.route('/notifications/mark-all-read', methods=['POST'])
def mark_all_notifications_read():
    if 'user' not in session:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    # Mark all unread notifications for the current user as read
    for notification in NOTIFICATIONS:
        if notification['user'] == session['user'] and notification['status'] == NOTIFICATION_STATUS['UNREAD']:
            notification['status'] = NOTIFICATION_STATUS['READ']
            notification['read_at'] = datetime.now()

    return jsonify({"success": True})

@app.route('/api/notifications/unread-count')
def get_unread_notification_count():
    if 'user' not in session:
        return jsonify({"count": 0})

    # Count unread notifications for the current user
    unread_count = len([n for n in NOTIFICATIONS if n['user'] == session['user'] and n['status'] == NOTIFICATION_STATUS['UNREAD']])

    return jsonify({"count": unread_count})

@app.route('/advanced-search')
def advanced_search():
    if 'user' not in session:
        return redirect(url_for('unified_login'))

    return render_template('advanced_search.html')

@app.route('/api/vans')
def api_get_vans():
    if 'user' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    # Add rating information to vans
    vans_with_ratings = []
    for van in VANS:
        van_copy = van.copy()
        # Get all approved reviews for this van
        van_reviews = [r for r in REVIEWS if r['van_id'] == van['id'] and r['status'] == REVIEW_STATUS['APPROVED']]

        # Calculate average rating
        if van_reviews:
            avg_rating = sum(r['rating'] for r in van_reviews) / len(van_reviews)
            van_copy['avg_rating'] = round(avg_rating, 1)
            van_copy['review_count'] = len(van_reviews)
        else:
            van_copy['avg_rating'] = 0
            van_copy['review_count'] = 0

        vans_with_ratings.append(van_copy)

    return jsonify({"vans": vans_with_ratings})

@app.route('/api/search-vans')
def api_search_vans():
    if 'user' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    # Get search parameters
    location = request.args.get('location', '').lower()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    min_price = request.args.get('min_price', type=int)
    max_price = request.args.get('max_price', type=int)
    capacity = request.args.get('capacity', type=int)
    category = request.args.get('category')
    fuel_type = request.args.get('fuel_type')
    transmission = request.args.get('transmission')
    amenities = request.args.get('amenities', '').split(',') if request.args.get('amenities') else []
    min_rating = request.args.get('min_rating', type=float)

    # Start with all vans
    filtered_vans = []

    for van in VANS:
        van_copy = van.copy()

        # Add rating information
        van_reviews = [r for r in REVIEWS if r['van_id'] == van['id'] and r['status'] == REVIEW_STATUS['APPROVED']]
        if van_reviews:
            avg_rating = sum(r['rating'] for r in van_reviews) / len(van_reviews)
            van_copy['avg_rating'] = round(avg_rating, 1)
            van_copy['review_count'] = len(van_reviews)
        else:
            van_copy['avg_rating'] = 0
            van_copy['review_count'] = 0

        # Apply filters
        if location and location not in van['location'].lower():
            continue

        if min_price and van['price'] < min_price:
            continue

        if max_price and van['price'] > max_price:
            continue

        if capacity and van['seats'] < capacity:
            continue

        if category and van.get('category') != category:
            continue

        if fuel_type and van.get('fuel_type') != fuel_type:
            continue

        if transmission and van.get('transmission') != transmission:
            continue

        if min_rating and van_copy['avg_rating'] < min_rating:
            continue

        # Check amenities
        if amenities and amenities != ['']:
            van_amenities = van.get('amenities', [])
            if not all(amenity in van_amenities for amenity in amenities):
                continue

        # Check date availability
        if start_date and end_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')

                # Check if van is available for the selected dates
                blocked_dates = van.get('blocked_dates', [])
                is_available = True

                for blocked_date_str in blocked_dates:
                    blocked_date = datetime.strptime(blocked_date_str, '%Y-%m-%d')
                    if start_dt <= blocked_date <= end_dt:
                        is_available = False
                        break

                if not is_available:
                    continue

            except ValueError:
                # Invalid date format, skip date filtering
                pass

        filtered_vans.append(van_copy)

    return jsonify({"vans": filtered_vans})

@app.route('/api/save-search', methods=['POST'])
def save_search():
    if 'user' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        data = request.get_json()
        search_name = data.get('search_name')
        search_description = data.get('search_description', '')
        search_criteria = data.get('search_criteria', {})
        email_alerts = data.get('email_alerts', False)

        if not search_name:
            return jsonify({"error": "Search name is required"}), 400

        # Create saved search
        search_id = len(SAVED_SEARCHES)
        saved_search = {
            'id': search_id,
            'user': session['user'],
            'name': search_name,
            'description': search_description,
            'criteria': search_criteria,
            'email_alerts': email_alerts,
            'created_at': datetime.now(),
            'last_used': datetime.now()
        }

        SAVED_SEARCHES.append(saved_search)

        return jsonify({"success": True, "search_id": search_id})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/saved-searches')
def get_saved_searches():
    if 'user' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    # Get saved searches for the current user
    user_searches = [s for s in SAVED_SEARCHES if s['user'] == session['user']]

    # Sort by last used (most recent first)
    user_searches.sort(key=lambda x: x['last_used'], reverse=True)

    return jsonify({"searches": user_searches})

@app.route('/api/delete-saved-search/<int:search_id>', methods=['DELETE'])
def delete_saved_search(search_id):
    if 'user' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    if search_id < len(SAVED_SEARCHES):
        search = SAVED_SEARCHES[search_id]

        # Check if this search belongs to the current user
        if search['user'] != session['user']:
            return jsonify({"error": "Access denied"}), 403

        # Remove the search (in a real app, you'd mark it as deleted)
        SAVED_SEARCHES[search_id] = None

        return jsonify({"success": True})

    return jsonify({"error": "Search not found"}), 404

@app.route('/api/toggle-favorite', methods=['POST'])
def toggle_favorite():
    if 'user' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        data = request.get_json()
        van_id = data.get('van_id')

        if van_id is None:
            return jsonify({"error": "Van ID is required"}), 400

        # Check if van exists
        van = next((v for v in VANS if v['id'] == van_id), None)
        if not van:
            return jsonify({"error": "Van not found"}), 404

        # Check if already favorited
        existing_favorite = next((f for f in FAVORITE_VANS if f['user'] == session['user'] and f['van_id'] == van_id), None)

        if existing_favorite:
            # Remove from favorites
            FAVORITE_VANS.remove(existing_favorite)
            is_favorited = False
        else:
            # Add to favorites
            favorite = {
                'id': len(FAVORITE_VANS),
                'user': session['user'],
                'van_id': van_id,
                'created_at': datetime.now()
            }
            FAVORITE_VANS.append(favorite)
            is_favorited = True

        return jsonify({"success": True, "is_favorited": is_favorited})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/favorites')
def get_favorites():
    if 'user' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    # Get favorite van IDs for the current user
    user_favorites = [f['van_id'] for f in FAVORITE_VANS if f['user'] == session['user']]

    # Get the actual van data
    favorite_vans = []
    for van in VANS:
        if van['id'] in user_favorites:
            van_copy = van.copy()

            # Add rating information
            van_reviews = [r for r in REVIEWS if r['van_id'] == van['id'] and r['status'] == REVIEW_STATUS['APPROVED']]
            if van_reviews:
                avg_rating = sum(r['rating'] for r in van_reviews) / len(van_reviews)
                van_copy['avg_rating'] = round(avg_rating, 1)
                van_copy['review_count'] = len(van_reviews)
            else:
                van_copy['avg_rating'] = 0
                van_copy['review_count'] = 0

            favorite_vans.append(van_copy)

    return jsonify({"vans": favorite_vans})

@app.route('/favorites')
def favorites_page():
    if 'user' not in session:
        return redirect(url_for('unified_login'))

    return render_template('favorites.html')

@app.route('/chat')
def chat_page():
    if 'user' not in session:
        return redirect(url_for('unified_login'))

    return render_template('chat.html')

@app.route('/api/chat/start', methods=['POST'])
def start_chat():
    if 'user' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        # Create new conversation
        conversation_id = len(CHAT_CONVERSATIONS)
        conversation = {
            'id': conversation_id,
            'user': session['user'],
            'subject': 'Support Chat',
            'status': CHAT_STATUS['ACTIVE'],
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'last_message': None,
            'assigned_agent': None
        }

        CHAT_CONVERSATIONS.append(conversation)

        # Create welcome message
        message_id = len(CHAT_MESSAGES)
        welcome_message = {
            'id': message_id,
            'conversation_id': conversation_id,
            'user': 'system',
            'message': 'Hello! How can we help you today?',
            'type': MESSAGE_TYPE['SYSTEM'],
            'timestamp': datetime.now(),
            'read': False
        }

        CHAT_MESSAGES.append(welcome_message)

        return jsonify({"success": True, "conversation_id": conversation_id})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/conversations')
def get_chat_conversations():
    if 'user' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    # Get conversations for the current user
    user_conversations = [c for c in CHAT_CONVERSATIONS if c['user'] == session['user']]

    # Sort by updated_at (most recent first)
    user_conversations.sort(key=lambda x: x['updated_at'], reverse=True)

    # Convert datetime objects to strings for JSON serialization
    conversations_data = []
    for conv in user_conversations:
        conv_data = conv.copy()
        conv_data['created_at'] = conv['created_at'].isoformat()
        conv_data['updated_at'] = conv['updated_at'].isoformat()
        conversations_data.append(conv_data)

    return jsonify({"conversations": conversations_data})

@app.route('/api/chat/messages/<int:conversation_id>')
def get_chat_messages(conversation_id):
    if 'user' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    # Check if conversation belongs to user
    conversation = next((c for c in CHAT_CONVERSATIONS if c['id'] == conversation_id and c['user'] == session['user']), None)
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404

    # Get messages for this conversation
    conversation_messages = [m for m in CHAT_MESSAGES if m['conversation_id'] == conversation_id]

    # Sort by timestamp
    conversation_messages.sort(key=lambda x: x['timestamp'])

    # Convert datetime objects to strings for JSON serialization
    messages_data = []
    for msg in conversation_messages:
        msg_data = msg.copy()
        msg_data['timestamp'] = msg['timestamp'].isoformat()
        messages_data.append(msg_data)

    return jsonify({"messages": messages_data})

@app.route('/api/chat/end/<int:conversation_id>', methods=['POST'])
def end_chat(conversation_id):
    if 'user' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    # Check if conversation belongs to user
    conversation = next((c for c in CHAT_CONVERSATIONS if c['id'] == conversation_id and c['user'] == session['user']), None)
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404

    # Update conversation status
    conversation['status'] = CHAT_STATUS['CLOSED']
    conversation['updated_at'] = datetime.now()

    # Add system message
    message_id = len(CHAT_MESSAGES)
    end_message = {
        'id': message_id,
        'conversation_id': conversation_id,
        'user': 'system',
        'message': 'Chat ended by user',
        'type': MESSAGE_TYPE['SYSTEM'],
        'timestamp': datetime.now(),
        'read': False
    }

    CHAT_MESSAGES.append(end_message)

    return jsonify({"success": True})

@app.route('/api/support/ticket', methods=['POST'])
def create_support_ticket():
    if 'user' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        subject = request.form.get('subject')
        priority = request.form.get('priority')
        category = request.form.get('category')
        description = request.form.get('description')

        if not all([subject, priority, category, description]):
            return jsonify({"error": "All fields are required"}), 400

        # Create support ticket
        ticket_id = len(SUPPORT_TICKETS)
        ticket = {
            'id': ticket_id,
            'user': session['user'],
            'subject': subject,
            'priority': priority,
            'category': category,
            'description': description,
            'status': TICKET_STATUS['OPEN'],
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'assigned_agent': None,
            'resolution': None,
            'attachments': []
        }

        # Handle file attachment if present
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file.filename:
                # In a real app, you would save the file and store the path
                ticket['attachments'].append({
                    'filename': file.filename,
                    'size': len(file.read()),
                    'uploaded_at': datetime.now()
                })

        SUPPORT_TICKETS.append(ticket)

        # Create notification for the user
        create_notification(
            user_email=session['user'],
            notification_type=NOTIFICATION_TYPE['SYSTEM'],
            title='Support Ticket Created',
            message=f'Your support ticket #{ticket_id} has been created and will be reviewed shortly.',
            related_id=ticket_id,
            related_type='ticket'
        )

        return jsonify({"success": True, "ticket_id": ticket_id})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/support-tickets')
def support_tickets_page():
    if 'user' not in session:
        return redirect(url_for('unified_login'))

    # Get tickets for the current user
    user_tickets = [t for t in SUPPORT_TICKETS if t['user'] == session['user']]

    # Sort by created_at (most recent first)
    user_tickets.sort(key=lambda x: x['created_at'], reverse=True)

    return render_template('support_tickets.html', tickets=user_tickets)

@app.route('/api/support/tickets')
def get_support_tickets():
    if 'user' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    # Get tickets for the current user
    user_tickets = [t for t in SUPPORT_TICKETS if t['user'] == session['user']]

    # Sort by created_at (most recent first)
    user_tickets.sort(key=lambda x: x['created_at'], reverse=True)

    # Convert datetime objects to strings for JSON serialization
    tickets_data = []
    for ticket in user_tickets:
        ticket_data = ticket.copy()
        ticket_data['created_at'] = ticket['created_at'].isoformat()
        ticket_data['updated_at'] = ticket['updated_at'].isoformat()
        tickets_data.append(ticket_data)

    return jsonify({"tickets": tickets_data})

@app.route('/unified_login', methods=['GET', 'POST'])
def unified_login():
    if session.get('user'):
        if session.get('role') == 'updater':
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

# Helper function to create notifications
def create_notification(user_email, notification_type, title, message, related_id=None, related_type=None):
    """
    Create a new notification for a user

    Args:
        user_email (str): The email of the user to notify
        notification_type (str): The type of notification (from NOTIFICATION_TYPE)
        title (str): The notification title
        message (str): The notification message
        related_id (int, optional): ID of the related object (booking, review, etc.)
        related_type (str, optional): Type of the related object ('booking', 'review', etc.)

    Returns:
        dict: The created notification object
    """
    notification_id = len(NOTIFICATIONS)
    notification = {
        'id': notification_id,
        'user': user_email,
        'type': notification_type,
        'title': title,
        'message': message,
        'status': NOTIFICATION_STATUS['UNREAD'],
        'created_at': datetime.now(),
        'read_at': None,
        'related_id': related_id,
        'related_type': related_type
    }

    NOTIFICATIONS.append(notification)

    # Emit socket event for real-time notification
    socketio.emit('notification', {
        'id': notification_id,
        'title': title,
        'message': message,
        'type': notification_type,
        'created_at': notification['created_at'].strftime('%Y-%m-%d %H:%M:%S')
    }, room=user_email)

    return notification

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    if 'user' in session:
        # Join a room with the user's email as the room name
        # This allows for user-specific notifications
        join_room(session['user'])

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')
    if 'user' in session:
        leave_room(session['user'])

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

# Event for review updates
@socketio.on('review_update')
def handle_review_update(data):
    # Broadcast the review update to all connected clients
    emit('review_update', data, broadcast=True)

# Event for review response updates
@socketio.on('review_response_update')
def handle_review_response_update(data):
    # Broadcast the review response update to all connected clients
    emit('review_response_update', data, broadcast=True)

# Event for marking notifications as read
@socketio.on('mark_notification_read')
def handle_mark_notification_read(data):
    if 'user' in session and 'notification_id' in data:
        notification_id = data['notification_id']
        notification = next((n for n in NOTIFICATIONS if n['id'] == notification_id and n['user'] == session['user']), None)

        if notification:
            notification['status'] = NOTIFICATION_STATUS['READ']
            notification['read_at'] = datetime.now()

            # Emit event to update notification status
            emit('notification_status_update', {
                'id': notification_id,
                'status': NOTIFICATION_STATUS['READ']
            }, room=session['user'])

# Update the book route to emit a socket event
@app.route('/book', methods=['POST'])
def book():
    if 'user' not in session:
        return redirect(url_for('unified_login'))

    try:
        van_id = int(request.form['van_id'])

        # Check if required fields are present
        if not request.form.get('start_date') or not request.form.get('end_date') or not request.form.get('passengers'):
            flash('Missing booking details. Please start from the home page to select your trip dates.', 'warning')
            return redirect(url_for('home'))

        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
        passengers = int(request.form['passengers'])

        # Validate dates
        if start_date >= end_date:
            flash('End date must be after start date.', 'danger')
            return redirect(url_for('home'))

        if start_date < datetime.now().date():
            flash('Start date cannot be in the past.', 'danger')
            return redirect(url_for('home'))

    except (ValueError, KeyError) as e:
        flash('Invalid booking data. Please try again.', 'danger')
        return redirect(url_for('home'))

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

        # Create notification for the user
        create_notification(
            user_email=session['user'],
            notification_type=NOTIFICATION_TYPE['BOOKING_CONFIRMED'],
            title='Booking Confirmed',
            message=f'Your booking for {van["name"]} from {start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")} has been confirmed.',
            related_id=booking_id,
            related_type='booking'
        )

        # Create notification for the van owner
        # In a real app, you would get the owner's email from the van object
        # For now, we'll just use a placeholder or admin email
        if session.get('role') != 'updater':  # Don't notify if the owner is booking their own van
            owner_email = "admin@example.com"  # This would be van['owner_email'] in a real app
            create_notification(
                user_email=owner_email,
                notification_type=NOTIFICATION_TYPE['BOOKING_CONFIRMED'],
                title='New Booking',
                message=f'You have a new booking for {van["name"]} from {start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")}.',
                related_id=booking_id,
                related_type='booking'
            )

        flash('Booking confirmed!', 'success')
        return redirect(url_for('booking_confirmation', booking_id=booking_id))
    else:
        flash('Van not available', 'danger')
        return redirect(url_for('list_vans'))

# Chat event handlers
@socketio.on('join_chat')
def handle_join_chat(data):
    if 'user' in session:
        user_email = session['user']
        join_room(f"chat_{user_email}")
        print(f"User {user_email} joined chat room")

@socketio.on('chat_message')
def handle_chat_message(data):
    if 'user' in session:
        user_email = session['user']
        conversation_id = data.get('conversation_id')
        message = data.get('message')
        message_type = data.get('type', MESSAGE_TYPE['USER'])

        if conversation_id is not None and message:
            # Store message
            message_id = len(CHAT_MESSAGES)
            chat_message = {
                'id': message_id,
                'conversation_id': conversation_id,
                'user': user_email,
                'message': message,
                'type': message_type,
                'timestamp': datetime.now(),
                'read': False
            }

            CHAT_MESSAGES.append(chat_message)

            # Update conversation
            conversation = next((c for c in CHAT_CONVERSATIONS if c['id'] == conversation_id), None)
            if conversation:
                conversation['last_message'] = message
                conversation['updated_at'] = datetime.now()

            # Emit message to support agents (in a real app, you'd have a support room)
            emit('chat_message', {
                'id': message_id,
                'conversation_id': conversation_id,
                'user': user_email,
                'message': message,
                'type': message_type,
                'timestamp': chat_message['timestamp'].isoformat()
            }, room=f"chat_{user_email}")

            # Simulate support response after a delay (for demo purposes)
            if message_type == MESSAGE_TYPE['USER']:
                socketio.start_background_task(simulate_support_response, conversation_id, user_email)

def simulate_support_response(conversation_id, user_email):
    """Simulate a support agent response for demo purposes"""
    import time
    time.sleep(2)  # Wait 2 seconds

    # Generate a simple response based on keywords
    last_message = None
    for msg in reversed(CHAT_MESSAGES):
        if msg['conversation_id'] == conversation_id and msg['type'] == MESSAGE_TYPE['USER']:
            last_message = msg['message'].lower()
            break

    response = "Thank you for contacting us. How can I help you today?"

    if last_message:
        if 'booking' in last_message:
            response = "I can help you with your booking. Could you please provide your booking reference number?"
        elif 'payment' in last_message:
            response = "I understand you're having payment issues. Let me help you resolve this. What specific problem are you experiencing?"
        elif 'cancel' in last_message:
            response = "I can help you with cancellation. Please note that our cancellation policy allows free cancellation up to 24 hours before your trip."
        elif 'van' in last_message or 'vehicle' in last_message:
            response = "I'd be happy to help you with van information. What would you like to know about our vehicles?"
        elif 'hello' in last_message or 'hi' in last_message:
            response = "Hello! Welcome to Tour Van Booking support. How can I assist you today?"

    # Create support message
    message_id = len(CHAT_MESSAGES)
    support_message = {
        'id': message_id,
        'conversation_id': conversation_id,
        'user': 'support',
        'message': response,
        'type': MESSAGE_TYPE['SUPPORT'],
        'timestamp': datetime.now(),
        'read': False
    }

    CHAT_MESSAGES.append(support_message)

    # Update conversation
    conversation = next((c for c in CHAT_CONVERSATIONS if c['id'] == conversation_id), None)
    if conversation:
        conversation['last_message'] = response
        conversation['updated_at'] = datetime.now()

    # Emit response to user
    socketio.emit('chat_message', {
        'id': message_id,
        'conversation_id': conversation_id,
        'user': 'support',
        'message': response,
        'type': MESSAGE_TYPE['SUPPORT'],
        'timestamp': support_message['timestamp'].isoformat()
    }, room=f"chat_{user_email}")

if __name__ == '__main__':
    socketio.run(app, debug=True)
