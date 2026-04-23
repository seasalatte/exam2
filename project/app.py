import os
import json
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  

def init_json_file(file_path: str) -> None:
    if not os.path.exists(file_path):
        try:
            initial_data = {"users": []}
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, indent=4, ensure_ascii=False)
        except IOError:
            pass

def read_users(file_path: str) -> dict:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"users": []}

def save_users(file_path: str, data: dict) -> bool:
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except IOError:
        return False
    
def validate_register(form_data: dict, users: list) -> dict:
    username = form_data.get("username", "").strip()
    email = form_data.get("email", "").strip()
    password = form_data.get("password", "").strip()
    phone = form_data.get("phone", "").strip()
    birthdate = form_data.get("birthdate", "").strip()

    if not all([username, email, password, birthdate]):
        return {"success": False, "error": "帳號、Email、密碼與生日為必填"}

    if "@" not in email or "." not in email:
        return {"success": False, "error": "Email 格式錯誤 (需含 @ 與 .)"}
    if not (6 <= len(password) <= 16):
        return {"success": False, "error": "密碼長度需在 6-16 位之間"}

    if phone:
        if len(phone) != 10 or not phone.startswith("09") or not phone.isdigit():
            return {"success": False, "error": "電話需為 10 碼數字且開頭為 09"}

    if any(u['email'] == email or u['username'] == username for u in users):
        return {"success": False, "error": "帳號或 Email 已被註冊"}

    return {"success": True, "data": form_data}

def verify_login(email: str, password: str, users: list) -> dict:
    for user in users:
        if user['email'] == email and user['password'] == password:
            return {"success": True, "data": user}
    return {"success": False, "error": "Email 或密碼錯誤"}

init_json_file('users.json')

@app.template_filter('mask_phone')
def mask_phone(phone_str):
    if len(phone_str) >= 10:
        return f"{phone_str[:4]}****{phone_str[8:]}"
    return phone_str 

@app.template_filter('format_tw_date')
def format_tw_date(date_str):
    try:
        year, month, day = date_str.split('-')
        minguo_year = int(year) - 1911
        return f"民國 {minguo_year} 年 {month} 月 {day} 日"
    except:
        return date_str

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register_route():
    if request.method == 'POST':
        full_db = read_users('users.json')
        result = validate_register(request.form.to_dict(), full_db['users'])
        
        if result['success']:
            full_db['users'].append(result['data'])
            save_users('users.json', full_db)
            return redirect(url_for('login_route'))
        return redirect(url_for('error_route', msg=result['error']))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login_route():
    if request.method == 'POST':
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        full_db = read_users('users.json')
        result = verify_login(email, password, full_db['users'])
        
        if result['success']:
            return redirect(url_for('welcome_route', username=result['data']['username']))
        return redirect(url_for('error_route', msg=result['error']))
    return render_template('login.html')

@app.route('/welcome/<username>')
def welcome_route(username):
    data = read_users('users.json')
    users_list = data.get('users',[])
    user_data = next((u for u in users_list if u['username'] == username), None)
    if not user_data:
        return redirect(url_for('error_route', msg="找不到該會員"))
    return render_template('welcome.html', user=user_data)

@app.route('/users')
def users_list_route():
    data = read_users('users.json')
    return render_template('users.html', users=data.get('users',[]))

@app.route('/error')
def error_route():
    message = request.args.get("msg", "發生未知錯誤")
    return render_template('error.html', message=message)

if __name__ == '__main__':
    app.run(debug=True)