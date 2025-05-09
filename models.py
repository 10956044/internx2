from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, login_manager
from datetime import datetime
import uuid

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    user_id = db.Column(db.String(10), primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    google_id = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image = db.Column(db.String(200), nullable=True)
    permission = db.Column(db.String(50), nullable=False, default='default user')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def get_id(self):
        return self.user_id
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    @staticmethod
    def generate_user_id():
        # 獲取最後一個用戶的 ID
        last_user = User.query.order_by(User.user_id.desc()).first()
        if last_user:
            # 從最後一個 ID 中提取數字部分
            last_num = int(last_user.user_id[1:])
            # 生成新的 ID
            new_num = last_num + 1
        else:
            # 如果沒有用戶，從 1 開始
            new_num = 1
        # 格式化新的 ID
        return f'U{new_num:02d}'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

class InterviewExperience(db.Model):
    __tablename__ = 'interview_experiences'
    
    experiences_id = db.Column(db.String(10), primary_key=True)
    user_id = db.Column(db.String(10), db.ForeignKey('users.user_id'), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(50), nullable=False)
    interview_date = db.Column(db.DateTime, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(db.Integer, nullable=False)
    result = db.Column(db.String(20), nullable=False)
    language = db.Column(db.String(20), nullable=False)
    written_test = db.Column(db.String(10), nullable=False)
    second_interview = db.Column(db.String(10), nullable=False)
    result_wait_time = db.Column(db.String(20), nullable=False)
    interview_process = db.Column(db.Text, nullable=False)
    questions_asked = db.Column(db.Text, nullable=False)
    advice = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, user_id, company, position, location, interview_date, rating, difficulty,
                 result, language, written_test, second_interview, result_wait_time,
                 interview_process, questions_asked, advice):
        self.experiences_id = f"Ex{str(uuid.uuid4())[:8]}"
        self.user_id = user_id
        self.company = company
        self.position = position
        self.location = location
        self.interview_date = interview_date
        self.rating = rating
        self.difficulty = difficulty
        self.result = result
        self.language = language
        self.written_test = written_test
        self.second_interview = second_interview
        self.result_wait_time = result_wait_time
        self.interview_process = interview_process
        self.questions_asked = questions_asked
        self.advice = advice 