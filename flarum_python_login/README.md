# Flarum Python Login Integration

## Overview
This small project demonstrates how to authenticate users against a Flarum community (`https://bbs.spark-app.store`) using Python.

- **`cli_login.py`** – Simple command‑line script that asks for username/email and password and prints the login result.
- **`app.py`** – Minimal Flask web application with a modern, glass‑morphism styled login page. After successful authentication it shows a dashboard with the Flarum user ID and token.
- **`requirements.txt`** – Required Python packages (`Flask`, `requests`).

## Setup
1. Open a terminal in the project directory:
   ```
   cd d:/Users/momen/Desktop/flarum/flarum_python_login
   ```
2. Install the dependencies:
   ```
   python -m pip install -r requirements.txt
   ```
   (You may need to use `pip3` depending on your environment.)

## Running the CLI script
```bash
python cli_login.py
```
Enter your Flarum username/email and password when prompted.

## Running the Flask web app
```bash
python app.py
```
Open your browser and navigate to `http://127.0.0.1:5000`. Use the login form to authenticate with your Flarum credentials.

## Notes
- The Flask app stores the token and user ID in the session for the duration of the browser session.
- Ensure the Flarum site is reachable from the machine running this script.
- For production use, replace the debug server with a proper WSGI server and secure the secret key.
