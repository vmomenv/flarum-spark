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
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flarum Guestbook</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background: #f0f2f5;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
        }
        .navbar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem 0;
            margin-bottom: 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .profile-card, .login-card {
            background: white;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            padding: 2.5rem;
            text-align: center;
            border: none;
        }
        .avatar-img {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            object-fit: cover;
            margin-bottom: 1.5rem;
            border: 4px solid #fff;
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
        .message-card {
            border: none;
            border-radius: 12px;
            transition: transform 0.2s;
            margin-bottom: 1rem;
        }
        .message-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(0,0,0,0.05);
        }
        .btn-primary {
            background: linear-gradient(to right, #667eea, #764ba2);
            border: none;
            border-radius: 10px;
            padding: 0.8rem 2rem;
            font-weight: 600;
        }
        .form-control {
            border-radius: 10px;
            border: 1px solid #ddd;
            padding: 0.8rem 1rem;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark">
        <div class="container d-flex justify-content-between">
            <a class="navbar-brand fw-bold" href="/">💬 Community Guestbook</a>
            {% if session.user_id %}
            <div class="d-flex align-items-center">
                <span class="text-white me-3 d-none d-sm-inline">Logged in as <strong>{{ session.username }}</strong></span>
                <a href="/logout" class="btn btn-outline-light btn-sm rounded-pill px-3">Logout</a>
            </div>
            {% endif %}
        </div>
    </nav>

    <div class="container pb-5">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show mb-4 rounded-3" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <div class="row g-4">
            <!-- Sidebar: User Info or Login -->
            <div class="col-lg-4 order-lg-2">
                <div class="sticky-top" style="top: 2rem; z-index: 100;">
                    {% if session.user_id %}
                        <!-- Authenticated User Profile -->
                        <div class="profile-card">
                            {% if session.avatar_url %}
                                <img src="{{ session.avatar_url }}" class="avatar-img" alt="Avatar">
                            {% else %}
                                <div class="avatar-img bg-primary d-flex align-items-center justify-content-center text-white fs-1 mx-auto">
                                    {{ session.username[0]|upper }}
                                </div>
                            {% endif %}
                            <h3 class="mb-1 fw-bold">{{ session.username }}</h3>
                            <div class="mb-3">
                                {% for group in session.groups %}
                                    <span class="group-badge" style="background-color: {{ group.color or '#6c757d' }}">
                                        {{ group.name }}
                                    </span>
                                {% endfor %}
                            </div>
                            <hr class="my-4">
                            <h5 class="text-start mb-3">Post a Message</h5>
                            <form action="/post_message" method="POST">
                                <textarea name="content" class="form-control mb-3" rows="4" placeholder="What would you like to say?" required></textarea>
                                <button type="submit" class="btn btn-primary w-100 shadow-sm">Post to Guestbook</button>
                            </form>
                        </div>
                    {% else %}
                        <!-- Login Form for Guests -->
                        <div class="login-card">
                            <h3 class="fw-bold mb-3">Join the convo</h3>
                            <p class="text-muted mb-4">Log in with your community account to post a message</p>
                            <form action="/login" method="POST">
                                <input type="text" name="username" class="form-control mb-3" placeholder="Username or Email" required>
                                <input type="password" name="password" class="form-control mb-4" placeholder="Password" required>
                                <button type="submit" class="btn btn-primary w-100 mb-3 shadow-sm">Sign In</button>
                            </form>
                            <div class="small text-muted">
                                Powered by <a href="{{ flarum_url }}" target="_blank" class="text-decoration-none">Flarum Auth</a>
                            </div>
                        </div>
                    {% endif %}
                </div>
            </div>

            <!-- Main Content: Message Board -->
            <div class="col-lg-8 order-lg-1">
                <div class="d-flex align-items-center mb-4">
                    <h2 class="fw-bold mb-0">Recent Activity</h2>
                    <span class="badge bg-white shadow-sm text-primary ms-3 rounded-pill px-3 py-2 fs-6 border">{{ message_list|length }} messages</span>
                </div>

                <div class="messages-list">
                    {% for msg in message_list %}
                        <div class="card message-card shadow-sm">
                            <div class="card-body p-4">
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
                                        <div class="d-flex justify-content-between align-items-start">
                                            <div>
                                                <h6 class="mb-0 fw-bold fs-5">{{ msg.username }}</h6>
                                                <small class="text-muted">{{ msg.timestamp }}</small>
                                            </div>
                                        </div>
                                        <div class="mt-3 text-dark fs-5" style="white-space: pre-wrap; word-break: break-all;">{{ msg.content }}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    {% endfor %}
                    
                    {% if not message_list %}
                        <div class="text-center py-5 bg-white rounded-4 shadow-sm">
                            <div class="fs-1 mb-3">🌿</div>
                            <h4 class="text-muted">It's quiet here...</h4>
                            <p class="text-muted">No messages yet. Be the first to start the conversation!</p>
                        </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
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
    # Fetch messages from database
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM messages ORDER BY timestamp DESC')
        messages = cursor.fetchall()
        
    return render_template_string(
        HOME_TEMPLATE,
        flarum_url=FLARUM_URL,
        message_list=messages
    )

@app.route('/login', methods=['POST'])
def login_process():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        flash('Username and password are required', 'error')
        return redirect(url_for('home'))
        
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
    else:
        flash(result['message'], 'error')
        
    return redirect(url_for('home'))

@app.route('/post_message', methods=['POST'])
def post_message():
    if 'user_id' not in session:
        flash('Please login to post a message', 'error')
        return redirect(url_for('home'))
    
    content = request.form.get('content')
    if not content:
        flash('Message content cannot be empty', 'error')
        return redirect(url_for('home'))
    
    # Store message in database
    with sqlite3.connect(DATABASE) as conn:
        conn.execute(
            'INSERT INTO messages (user_id, username, avatar_url, content) VALUES (?, ?, ?, ?)',
            (session['user_id'], session['username'], session['avatar_url'], content)
        )
    
    flash('Message posted successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    print(f"Starting Flarum Auth Integration App...")
    print(f"Target Flarum Community: {FLARUM_URL}")
    print(f"Access the app at: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
