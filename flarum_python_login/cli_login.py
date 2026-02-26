import requests

FLARUM_URL = "https://bbs.spark-app.store"

def login_to_flarum(username, password):
    url = f"{FLARUM_URL}/api/token"
    payload = {
        "identification": username,
        "password": password
    }
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            user_id = data.get("userId")
            print(f"✅ Login successful!")
            print(f"Token: {token}")
            print(f"User ID: {user_id}")
            return True, token
        else:
            print(f"❌ Login failed! Status Code: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error Details: {error_data}")
            except:
                print(f"Response text: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ An error occurred during request: {e}")
        return False, None

if __name__ == "__main__":
    print(f"=== Flarum Authenticator ({FLARUM_URL}) ===")
    user = input("Enter Flarum Username or Email: ")
    pwd = input("Enter Password: ")
    
    print("Verifying credentials...")
    login_to_flarum(user, pwd)
