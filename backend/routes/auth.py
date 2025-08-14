from flask import Blueprint, request, jsonify, current_app
from ..services.firebase_service import create_user, get_user_by_email
import jwt
import datetime
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'message': 'Token eksik!'}), 401
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user_uid = data['user_id']
        except Exception as e:
            return jsonify({'message': f'Token geçersiz veya süresi dolmuş: {e}'}), 401
        return f(current_user_uid, *args, **kwargs)
    return decorated

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    display_name = data.get('name')

    if not email or not password or not display_name:
        return jsonify({'message': 'E-posta, şifre ve isim gerekli!'}), 400

    if get_user_by_email(email):
        return jsonify({'message': 'Bu e-posta zaten kayıtlı.'}), 409

    try:
        user = create_user(email, password, display_name)
        return jsonify({'message': 'Kayıt başarılı!', 'user_id': user['uid']}), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password') # Frontend'den gelen şifre (Firebase Auth Client SDK tarafından doğrulanmalı)

    if not email or not password:
        return jsonify({'message': 'E-posta ve şifre gerekli!'}), 400

    user_record = get_user_by_email(email)
    if not user_record: # Kullanıcı yoksa veya şifre yanlışsa (simülasyon)
        return jsonify({'message': 'Yanlış e-posta veya şifre.'}), 401
    
    # Gerçek uygulamada Firebase Client SDK ile şifre doğrulanır ve ID token alınır.
    # Burada basitçe kullanıcı varsa giriş başarılı kabul ediyoruz.
    # Gelişmiş doğrulama için Firebase Admin SDK ile id_token doğrulama yapılmalı.
    # Örneğin: auth.verify_id_token(id_token)

    token = jwt.encode({
        'user_id': user_record['uid'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60)
    }, current_app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({'token': token, 'user_id': user_record['uid'], 'display_name': user_record['display_name']}), 200

