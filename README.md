# Tour Van Booking - Python Version

This is a Python/Flask implementation of the Tour Van Booking application.

## Features

- User authentication with Firebase and email verification
- Role-based access control (regular users and van owners)
- Real-time booking updates using Socket.IO
- Van listing and booking functionality
- Admin dashboard for van owners
- OTP verification for signup

## Prerequisites

- Python 3.8 or higher
- Flask
- Firebase Admin SDK
- Socket.IO

## Setup and Installation

1. Create a virtual environment:

```bash
python -m venv venv
```

2. Activate the virtual environment:

```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up Firebase:
   - Create a Firebase project
   - Download the service account key and save it as `firebase_config.json`
   - Enable Email/Password authentication in Firebase

5. Create a `.env` file with the following content:

```
SECRET_KEY=your_secret_key_here
FIREBASE_API_KEY=your_firebase_api_key
```

6. Run the application:

```bash
python app.py
```

7. Open your browser and navigate to `http://localhost:5000`

## Project Structure

- `app.py` - Main application file
- `templates/` - HTML templates
- `static/` - Static assets (CSS, JS, images)
- `utils/` - Utility functions
  - `email_utils.py` - Email and OTP functionality

## Implementation Details

This Python version uses:

1. **Flask**: A lightweight WSGI web application framework
2. **Firebase**: For authentication and user management
3. **Socket.IO**: For real-time updates
4. **Jinja2**: For HTML templating
5. **OTP Verification**: For secure signup process

## Demo Accounts

- Regular User:
  - Email: user@example.com
  - Password: password123
  
- Van Owner (Admin):
  - Email: admin@example.com
  - Password: admin123

## Notes

This is a demonstration project and not intended for production use. In a real application, you would:

1. Use a proper database instead of in-memory storage
2. Implement more robust error handling
3. Add comprehensive logging
4. Use HTTPS for secure communication
5. Implement proper email sending functionality
