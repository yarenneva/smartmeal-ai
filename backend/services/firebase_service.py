import firebase_admin
from firebase_admin import credentials, auth, firestore
import os
import json

# Firebase Admin SDK başlatma
# serviceAccountKey.json dosyasının backend klasöründe olduğundan emin olun
# cred = credentials.Certificate(os.path.join(os.path.dirname(__file__), '..', 'serviceAccountKey.json'))

# Ortam değişkeninden Firebase Service Account Key'i oku
try:
    firebase_service_account_info = json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY'))
    cred = credentials.Certificate(firebase_service_account_info)
    firebase_admin.initialize_app(cred)
except Exception as e:
    print(f"Firebase başlatılırken hata oluştu: {e}")

db = firestore.client()

def create_user(email, password, display_name):
    try:
        user = auth.create_user(email=email, password=password, display_name=display_name)
        # Firestore'a kullanıcı bilgilerini kaydet
        db.collection('users').document(user.uid).set({
            'email': email,
            'display_name': display_name
        })
        return {"uid": user.uid, "email": user.email, "display_name": user.display_name}
    except Exception as e:
        raise Exception(f"Kullanıcı oluşturulurken hata: {e}")

def get_user_by_email(email):
    try:
        user = auth.get_user_by_email(email)
        return {"uid": user.uid, "email": user.email, "display_name": user.display_name}
    except Exception as e:
        return None

def verify_password(email, password):
    try:
        # Firebase Auth'ta doğrudan şifre doğrulama yok.
        # Bu genellikle istemci tarafında yapılır (client SDK ile).
        # Ancak backend için bir simülasyon yapabiliriz veya
        # sadece email ile kullanıcı olup olmadığını kontrol edebiliriz.
        # Gerçek bir uygulamada, istemciden gelen token'ı doğrularız.
        # Örneğin: auth.verify_id_token(id_token)

        user = auth.get_user_by_email(email)
        # Basit bir kontrol, gerçekte Firebase Auth REST API kullanılmalı
        # veya istemciden gelen ID token doğrulanmalı
        return user is not None
    except Exception:
        return False

def save_recipe(user_id, recipe_data):
    try:
        recipes_ref = db.collection('users').document(user_id).collection('recipes')
        # recipe_data'ya user_id'yi de ekle
        recipe_data['user_id'] = user_id
        doc_ref = recipes_ref.add(recipe_data)
        return doc_ref[1].id # Returns the ID of the new document
    except Exception as e:
        raise Exception(f"Tarif kaydedilirken hata: {e}")

def get_user_recipes(user_id):
    try:
        recipes_ref = db.collection('users').document(user_id).collection('recipes')
        recipes = []
        for doc in recipes_ref.stream():
            recipe_data = doc.to_dict()
            recipe_data['id'] = doc.id # Add document ID to the data
            recipes.append(recipe_data)
        return recipes
    except Exception as e:
        raise Exception(f"Kullanıcı tarifleri getirilirken hata: {e}")

def delete_recipe(user_id, recipe_id):
    try:
        # Önce tarifin bu kullanıcıya ait olduğunu doğrula
        recipe_ref = db.collection('users').document(user_id).collection('recipes').document(recipe_id)
        recipe_doc = recipe_ref.get()
        
        if not recipe_doc.exists:
            return False
        
        # Tarifi sil
        recipe_ref.delete()
        return True
    except Exception as e:
        raise Exception(f"Tarif silinirken hata: {e}")