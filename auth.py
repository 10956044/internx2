from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from authlib.integrations.flask_client import OAuth
import os

auth = Blueprint('auth', __name__)
oauth = OAuth()
# Google OAuth 註冊
@auth.record_once
def init_oauth(state):
    app = state.app
    oauth.init_app(app)
    oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    },
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    fetch_userinfo=True
)

# Google登入按鈕
@auth.route('/login/google')
def google_login():
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)
# Google 登入回傳處理
@auth.route('/login/callback')
def google_callback():
    token = oauth.google.authorize_access_token()

    if 'userinfo' not in token:
        flash('無法從 Google 獲取用戶資料', 'error')
        return redirect(url_for('auth.login'))

    user_info = token['userinfo']
    session['user'] = user_info  # 如果你有要前端取用

    email = user_info.get('email')
    username = user_info.get('name')
    image = user_info.get('picture')

    # 查詢或創建使用者
    user = User.query.filter_by(email=email).first()
    if not user:
        user_id = User.generate_user_id()
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            image=image,
            permission='default user',
            # is_oauth_user=True  # 請確認你的模型有這欄位
        )
        db.session.add(user)
        db.session.commit()

    login_user(user)
    flash('成功使用 Google 登入', 'success')
    return redirect(url_for('profile'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        print(f"收到註冊請求: username={username}, email={email}")  # 調試信息

        # 檢查密碼是否匹配
        if password != confirm_password:
            flash('密碼不匹配', 'error')
            return redirect(url_for('auth.register'))

        # 檢查郵箱是否已存在
        user = User.query.filter_by(email=email).first()
        if user:
            flash('該電子郵件已被註冊', 'error')
            return redirect(url_for('auth.register'))

        # 生成用戶ID
        user_id = User.generate_user_id()
        print(f"生成的用戶ID: {user_id}")  # 調試信息

        # 創建新用戶
        new_user = User(
            user_id=user_id,
            username=username,
            email=email,
            permission='default user'
        )
        new_user.set_password(password)

        try:
            print("嘗試添加用戶到資料庫...")  # 調試信息
            db.session.add(new_user)
            print("嘗試提交事務...")  # 調試信息
            db.session.commit()
            print("用戶成功添加到資料庫")  # 調試信息
            flash('註冊成功！請登入', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            print(f"註冊失敗，錯誤信息: {str(e)}")  # 調試信息
            db.session.rollback()
            flash('註冊失敗，請稍後再試', 'error')
            return redirect(url_for('auth.register'))

    return render_template('register.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        print(f"收到登入請求: email={email}")  # 調試信息

        user = User.query.filter_by(email=email).first()

        # 檢查用戶是否存在且密碼是否正確
        if not user or not user.check_password(password):
            flash('電子郵件或密碼錯誤', 'error')
            return redirect(url_for('auth.login'))

        # 登入用戶
        login_user(user, remember=remember)
        print(f"用戶 {user.username} 登入成功")  # 調試信息
        
        # 獲取用戶想要訪問的頁面
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('index')
            
        flash('登入成功！歡迎回來', 'success')
        return redirect(next_page)

    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已成功登出', 'success')
    return redirect(url_for('index')) 