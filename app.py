from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
import os
from dotenv import load_dotenv
from extensions import db, login_manager
from models import User, InterviewExperience
from flask_migrate import Migrate
from auth import auth
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime

# 載入環境變數
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
    
    # 資料庫配置
    if os.environ.get('DATABASE_URL'):
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 配置上傳文件夾
    app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # 確保上傳文件夾存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # 初始化擴展
    db.init_app(app)
    login_manager.init_app(app)
    
    # 註冊認證藍圖
    app.register_blueprint(auth)

    migrate = Migrate(app, db)

    # 創建資料庫表
    with app.app_context():
        db.create_all()

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    # 首頁路由
    @app.route('/')
    def index():
        return render_template('index.html')

    # 找實習頁面
    @app.route('/internships')
    def internships():
        return render_template('internships.html')

    # 職涯諮詢頁面
    @app.route('/consulting')
    def consulting():
        return render_template('consulting.html')

    # 經驗分享頁面
    @app.route('/experience')
    def experience():
        # 獲取所有面試經驗，按時間倒序排列
        experiences = InterviewExperience.query.order_by(InterviewExperience.created_at.desc()).all()
        return render_template('experience.html', experiences=experiences)

    @app.route('/experience/<experience_id>')
    def experience_detail(experience_id):
        # 根據 ID 獲取特定面試經驗
        experience = InterviewExperience.query.get_or_404(experience_id)
        return render_template('experience_detail.html', experience=experience)

    # 個人資料頁面
    @app.route('/profile')
    @login_required
    def profile():
        return render_template('profile.html')

    # 更新個人資料
    @app.route('/update_profile', methods=['POST'])
    @login_required
    def update_profile():
        username = request.form.get('username')
        
        if not username:
            flash('用戶名不能為空', 'error')
            return redirect(url_for('profile'))
        
        try:
            current_user.username = username
            db.session.commit()
            flash('個人資料更新成功', 'success')
        except Exception as e:
            db.session.rollback()
            flash('更新失敗，請稍後再試', 'error')
        
        return redirect(url_for('profile'))

    # 更新密碼
    @app.route('/update_password', methods=['POST'])
    @login_required
    def update_password():
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # 驗證目前密碼
        if not current_user.check_password(current_password):
            flash('目前密碼錯誤', 'error')
            return redirect(url_for('profile'))
        
        # 驗證新密碼
        if not new_password:
            flash('新密碼不能為空', 'error')
            return redirect(url_for('profile'))
        
        if new_password != confirm_password:
            flash('兩次輸入的新密碼不一致', 'error')
            return redirect(url_for('profile'))
        
        try:
            current_user.set_password(new_password)
            db.session.commit()
            flash('密碼更新成功', 'success')
        except Exception as e:
            db.session.rollback()
            flash('更新失敗，請稍後再試', 'error')
        
        return redirect(url_for('profile'))

    # 更新頭像
    @app.route('/update_avatar', methods=['POST'])
    @login_required
    def update_avatar():
        if 'avatar' not in request.files:
            flash('沒有選擇文件', 'error')
            return redirect(url_for('profile'))
        
        file = request.files['avatar']
        if file.filename == '':
            flash('沒有選擇文件', 'error')
            return redirect(url_for('profile'))
        
        if file and allowed_file(file.filename):
            # 生成安全的文件名
            filename = secure_filename(file.filename)
            # 添加唯一標識符
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            # 保存文件
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            try:
                # 更新用戶頭像路徑
                current_user.image = f"/static/uploads/{unique_filename}"
                db.session.commit()
                flash('頭像更新成功', 'success')
            except Exception as e:
                db.session.rollback()
                flash('更新失敗，請稍後再試', 'error')
        else:
            flash('不支持的文件類型', 'error')
        
        return redirect(url_for('profile'))

    # 面試經驗分享 - 基本資訊頁面
    @app.route('/interview/basic', methods=['GET'])
    @login_required
    def interview_basic():
        return render_template('interview_basic.html')

    # 面試經驗分享 - 詳細內容頁面
    @app.route('/interview/detail', methods=['POST'])
    @login_required
    def interview_detail():
        # 獲取表單數據
        company = request.form.get('company')
        position = request.form.get('position')
        location = request.form.get('location')
        interview_date = request.form.get('interview_date')
        rating = request.form.get('rating')
        difficulty = request.form.get('difficulty')
        result = request.form.get('result')
        language = request.form.get('language')
        written_test = request.form.get('written_test')
        second_interview = request.form.get('second_interview')
        result_wait_time = request.form.get('result_wait_time')

        # 將數據傳遞到詳細內容頁面
        return render_template('interview_detail.html',
            company=company,
            position=position,
            location=location,
            interview_date=interview_date,
            rating=rating,
            difficulty=difficulty,
            result=result,
            language=language,
            written_test=written_test,
            second_interview=second_interview,
            result_wait_time=result_wait_time
        )

    # 提交面試經驗
    @app.route('/interview/submit', methods=['POST'])
    @login_required
    def submit_interview():
        try:
            # 獲取所有表單數據
            company = request.form.get('company')
            position = request.form.get('position')
            location = request.form.get('location')
            interview_date_str = request.form.get('interview_date')
            rating = request.form.get('rating')
            difficulty = request.form.get('difficulty')
            result = request.form.get('result')
            language = request.form.get('language')
            written_test = request.form.get('written_test')
            second_interview = request.form.get('second_interview')
            result_wait_time = request.form.get('result_wait_time')
            interview_process = request.form.get('interview_process')
            questions_asked = request.form.get('questions_asked')
            advice = request.form.get('advice')

            # 轉換日期字符串為 datetime 對象
            try:
                interview_date = datetime.strptime(interview_date_str, '%Y-%m-%d')
            except ValueError as e:
                flash('日期格式錯誤', 'error')
                return redirect(url_for('interview_basic'))

            # 生成經驗ID
            last_experience = db.session.query(InterviewExperience).order_by(InterviewExperience.experiences_id.desc()).first()
            if last_experience:
                last_id = int(last_experience.experiences_id[2:])
                new_id = f"Ex{str(last_id + 1).zfill(2)}"
            else:
                new_id = "Ex01"

            # 創建新的面試經驗記錄
            new_experience = InterviewExperience(
                experiences_id=new_id,
                user_id=current_user.user_id,
                company=company,
                position=position,
                location=location,
                interview_date=interview_date,
                rating=rating,
                difficulty=difficulty,
                result=result,
                language=language,
                written_test=written_test,
                second_interview=second_interview,
                result_wait_time=result_wait_time,
                interview_process=interview_process,
                questions_asked=questions_asked,
                advice=advice,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            # 保存到資料庫
            db.session.add(new_experience)
            db.session.commit()

            flash('面試經驗分享成功！', 'success')
            return redirect(url_for('experience'))

        except Exception as e:
            db.session.rollback()
            print(f"Error in submit_interview: {str(e)}")  # 添加錯誤日誌
            flash(f'分享失敗：{str(e)}', 'error')
            return redirect(url_for('interview_basic'))

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True,threaded=True) 