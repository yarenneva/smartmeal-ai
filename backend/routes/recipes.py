from flask import Blueprint, request, jsonify
from ..services.firebase_service import save_recipe, get_user_recipes, delete_recipe
from .auth import token_required

recipes_bp = Blueprint('recipes', __name__)

@recipes_bp.route('/save', methods=['POST'])
@token_required
def save_user_recipe(current_user_uid):
    data = request.get_json()
    if not data:
        return jsonify({'message': 'İstek gövdesi boş.'}), 400
    
    # Frontend'den beklenen tarif formatı
    required_fields = ["tarif_adi", "malzemeler", "kalori", "tarih", "diyet_tipi", "full_recipe_markdown"]
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Eksik tarif bilgisi.'}), 400

    try:
        recipe_id = save_recipe(current_user_uid, data)
        return jsonify({'message': 'Tarif başarıyla kaydedildi!', 'recipe_id': recipe_id}), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@recipes_bp.route('/user/<user_id>', methods=['GET'])
@token_required
def get_recipes(current_user_uid, user_id):
    if current_user_uid != user_id:
        return jsonify({'message': 'Erişim engellendi.'}), 403
    try:
        recipes = get_user_recipes(user_id)
        return jsonify(recipes), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@recipes_bp.route('/<recipe_id>', methods=['DELETE'])
@token_required
def delete_user_recipe(current_user_uid, recipe_id):
    try:
        # Tarifin gerçekten oturum açmış kullanıcıya ait olup olmadığını kontrol etmek için
        # tarifin user_id alanını kontrol etmek gerekebilir. Ancak Firebase güvenlik kuralları
        # genellikle buna izin verir. save_recipe içinde user_id zaten kayıtlı.
        success = delete_recipe(current_user_uid, recipe_id)
        if success:
            return jsonify({'message': 'Tarif başarıyla silindi.'}), 200
        else:
            return jsonify({'message': 'Tarif bulunamadı veya silinemedi.'}), 404
    except Exception as e:
        return jsonify({'message': str(e)}), 500

