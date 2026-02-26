from flask import Flask, render_template_string, request, session, redirect, url_for, flash
import requests
import secrets
import sqlite3
from datetime import datetime

app = Flask(__name__)
# Generate a random secret key for session management
app.secret_key = secrets.token_hex(16)

# Your Flarum forum URL
FLARUM_URL = "https://bbs.spark-app.store"
DATABASE = 'guestbook.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                avatar_url TEXT,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    print("Database initialized.")

init_db()

# HTML Templates encoded as strings for simplicity
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login with Flarum</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .login-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);
            padding: 40px;
            width: 100%;
            max-width: 400px;
            transition: transform 0.3s;
        }
        .login-card:hover {
            transform: translateY(-5px);
        }
        .brand-logo {
            text-align: center;
            margin-bottom: 30px;
        }
        .brand-logo h2 {
            color: #333;
            font-weight: 700;
        }
        .form-control {
            border-radius: 10px;
            padding: 12px 15px;
            margin-bottom: 20px;
            border: 1px solid #ddd;
        }
        .form-control:focus {
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.3);
            border-color: #667eea;
        }
        .btn-login {
            background: linear-gradient(to right, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 12px;
            width: 100%;
            font-weight: 600;
            font-size: 16px;
            transition: opacity 0.3s;
        }
        .btn-login:hover {
            opacity: 0.9;
            color: white;
        }
        .flarum-tag {
            text-align: center;
            margin-top: 20px;
            font-size: 14px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="login-card">
        <div class="brand-logo">
            <h2>Welcome Back</h2>
            <p class="text-muted">Sign in with your community account</p>
        </div>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <form method="POST" action="/login">
            <div class="form-group">
                <input type="text" class="form-control" name="username" placeholder="Username or Email" required>
            </div>
            <div class="form-group">
                <input type="password" class="form-control" name="password" placeholder="Password" required>
            </div>
            <button type="submit" class="btn btn-login">Sign In</button>
        </form>
        
        <div class="flarum-tag">
            Powered by <a href="{{ flarum_url }}" target="_blank">Flarum Authentication</a>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background-color: #f8f9fa;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .navbar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .dashboard-content {
            margin-top: 50px;
        }
        .profile-card {
            background: white;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.05);
            padding: 30px;
            text-align: center;
        }
        .avatar-img {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            object-fit: cover;
            margin-bottom: 20px;
            border: 3px solid #fff;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }
        .group-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            color: white;
            margin: 2px;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark shadow-sm">
        <div class="container">
            <a class="navbar-brand" href="#">Flarum Message Board</a>
            <div class="d-flex">
                <span class="navbar-text text-white me-3">
                    Hello, {{ username }}
                </span>
                <a href="/logout" class="btn btn-outline-light btn-sm">Logout</a>
            </div>
        </div>
    </nav>

    <div class="container dashboard-content">
        <div class="row">
            <!-- Sidebar: Profile Card -->
            <div class="col-md-4">
                <div class="profile-card mb-4 shadow">
                    {% if avatar_url %}
                        <img src="{{ avatar_url }}" class="avatar-img" alt="Avatar">
                    {% else %}
                        <div class="avatar-img bg-primary d-flex align-items-center justify-content-center text-white fs-1 mx-auto" style="width: 100px; height: 100px; border-radius: 50%;">
                            {{ username[0]|upper }}
                        </div>
                    {% endif %}
                    
                    <h3 class="mt-3">{{ username }}</h3>
                    
                    <div class="mb-3">
                        {% for group in groups %}
                            <span class="group-badge" style="background-color: {{ group.color or '#6c757d' }}">
                                {{ group.name }}
                            </span>
                        {% endfor %}
                    </div>

                    <hr>
                    <div class="text-start mt-3 small">
                        <p><strong>Flarum User ID:</strong> <span class="badge bg-secondary">{{ user_id }}</span></p>
                        <p class="text-muted">Authenticated via bbs.spark-app.store</p>
                    </div>
                </div>
            </div>

            <!-- Main Content: Message Board -->
            <div class="col-md-8">
                <div class="card shadow mb-4 border-0">
                    <div class="card-body p-4">
                        <h5 class="card-title mb-4">Leave a message</h5>
                        <form action="/post_message" method="POST">
                            <div class="mb-3">
                                <textarea name="content" class="form-control border-0 bg-light" rows="3" placeholder="Write something..." required style="resize: none;"></textarea>
                            </div>
                            <button type="submit" class="btn btn-primary px-4 fw-bold" style="border-radius: 10px;">Post Message</button>
                        </form>
                    </div>
                </div>

                <div class="messages-list">
                    <h5 class="mb-4 d-flex align-items-center">
                        Recent Messages 
                        <span class="badge bg-primary ms-2 rounded-pill fs-6">{{ messages|length }}</span>
                    </h5>
                    
                    {% for msg in messages %}
                        <div class="card shadow-sm mb-3 border-0" style="border-radius: 15px;">
                            <div class="card-body p-3">
                                <div class="d-flex">
                                    <div class="me-3">
                                        {% if msg.avatar_url %}
                                            <img src="{{ msg.avatar_url }}" width="50" height="50" class="rounded-circle shadow-sm" alt="Avatar">
                                        {% else %}
                                            <div class="rounded-circle bg-secondary d-flex align-items-center justify-content-center text-white shadow-sm" style="width: 50px; height: 50px; font-weight: bold;">
                                                {{ msg.username[0]|upper }}
                                            </div>
                                        {% endif %}
                                    </div>
                                    <div class="flex-grow-1">
                                        <div class="d-flex justify-content-between align-items-center">
                                            <h6 class="mb-0 fw-bold">{{ msg.username }}</h6>
                                            <small class="text-muted">{{ msg.timestamp }}</small>
                                        </div>
                                        <div class="mt-2 text-dark" style="word-break: break-word; line-height: 1.5;">
                                            {{ msg.content }}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    {% endfor %}
                    
                    {% if not messages %}
                        <div class="text-center text-muted p-5 bg-white rounded shadow-sm">
                            <i class="fs-1 mb-3 d-block">💬</i>
                            No messages yet. Be the first to share your thoughts!
                        </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

def verify_flarum_credentials(username, password):
    """
    Calls the Flarum REST API to verify user credentials.
    """
    url = f"{FLARUM_URL}/api/token"
    payload = {
        "identification": username,
        "password": password
    }
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "token": data.get("token"),
                "user_id": data.get("userId")
            }
        else:
            return {
                "success": False,
                "message": "Invalid username or password"
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "message": f"Connection error to Flarum: {str(e)}"
        }

def get_flarum_user_details(user_id, token):
    """
    Fetches detailed user information including avatar and groups.
    """
    url = f"{FLARUM_URL}/api/users/{user_id}?include=groups"
    headers = {
        "Authorization": f"Token {token}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            user_data = data.get("data", {})
            attributes = user_data.get("attributes", {})
            
            # Extract avatar
            avatar_url = attributes.get("avatarUrl")
            
            # Extract groups from included section
            groups = []
            included = data.get("included", [])
            for item in included:
                if item.get("type") == "groups":
                    group_attrs = item.get("attributes", {})
                    groups.append({
                        "name": group_attrs.get("nameSingular"),
                        "color": group_attrs.get("color"),
                        "icon": group_attrs.get("icon")
                    })
            
            return {
                "avatar_url": avatar_url,
                "groups": groups
            }
    except Exception as e:
        print(f"Error fetching user details: {e}")
    
    return {"avatar_url": None, "groups": []}

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login_page'))

@app.route('/login', methods=['GET'])
def login_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template_string(LOGIN_TEMPLATE, flarum_url=FLARUM_URL)

@app.route('/login', methods=['POST'])
def login_process():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        flash('Username and password are required', 'error')
        return redirect(url_for('login_page'))
        
    # Verify with Flarum
    result = verify_flarum_credentials(username, password)
    
    if result['success']:
        # Store basic user info
        session['user_id'] = result['user_id']
        session['username'] = username
        session['flarum_token'] = result['token']
        
        # Fetch detailed info (avatar, groups)
        details = get_flarum_user_details(result['user_id'], result['token'])
        session['avatar_url'] = details['avatar_url']
        session['groups'] = details['groups']
        
        flash('Successfully logged in!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash(result['message'], 'error')
        return redirect(url_for('login_page'))

@app.route('/dashboard')
def dashboard():
    # Keep user logged out if no session exists
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    # Fetch messages from database
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM messages ORDER BY timestamp DESC')
        messages = cursor.fetchall()
        
    return render_template_string(
        DASHBOARD_TEMPLATE,
        username=session.get('username'),
        user_id=session.get('user_id'),
        token=session.get('flarum_token'),
        avatar_url=session.get('avatar_url'),
        groups=session.get('groups'),
        flarum_url=FLARUM_URL,
        messages=messages
    )

@app.route('/post_message', methods=['POST'])
def post_message():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    content = request.form.get('content')
    if not content:
        flash('Message content cannot be empty', 'error')
        return redirect(url_for('dashboard'))
    
    # Store message in database
    with sqlite3.connect(DATABASE) as conn:
        conn.execute(
            'INSERT INTO messages (user_id, username, avatar_url, content) VALUES (?, ?, ?, ?)',
            (session['user_id'], session['username'], session['avatar_url'], content)
        )
    
    flash('Message posted successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    print(f"Starting Flarum Auth Integration App...")
    print(f"Target Flarum Community: {FLARUM_URL}")
    print(f"Access the app at: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
