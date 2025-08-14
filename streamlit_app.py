import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from typing import Dict, Any
import re
from datetime import date
import requests

# Initialize session state variables
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_info" not in st.session_state:
    st.session_state.user_info = {}
if "users" not in st.session_state:
    st.session_state.users = {}
if "liked_recipes" not in st.session_state:
    st.session_state.liked_recipes = []
# Ensure generated_recipe_text is initialized for proper display logic
if 'generated_recipe_text' not in st.session_state:
    st.session_state.generated_recipe_text = ""
if 'last_generated_recipe_details' not in st.session_state:
    st.session_state.last_generated_recipe_details = None
# For controlling which section is displayed in the main content area
if 'current_main_view' not in st.session_state:
    st.session_state.current_main_view = "recipe_generation" # Default view

# BACKEND_URL = "http://localhost:5000"
BACKEND_URL = st.secrets["BACKEND_URL"]

# load_dotenv(dotenv_path=os.path.join(os.getcwd(), '.env'))
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

st.set_page_config(page_title="SmartMeal AI 🍽️", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 3em;
        color: #FF69B4; /* Pembe */
        text-align: center;
        margin-bottom: 0.5em;
        text-shadow: 2px 2px 4px #FFDAB9; /* Şeftali tonu gölge */
    }
    .stApp {
        background: linear-gradient(to right, #FFD1DC, #ACE1AF); /* Pembe-yeşil degrade */
        color: #333333; /* Koyu metin */
    }
    .st-emotion-cache-1wv8t4m { /* Sidebar background */
        background-color: #f0f2f6; /* Açık gri tonu */
        border-right: 1px solid #e0e0e0;
        padding: 20px;
    }
    .stButton>button { /* Button styling */
        background-color: #FF69B4;
        color: white;
        border-radius: 10px;
        padding: 10px 20px;
        font-size: 1.1em;
        border: none;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
        transition: all 0.3s ease-in-out;
    }
    .stButton>button:hover {
        background-color: #FF1493; /* Koyu pembe */
        transform: translateY(-2px);
    }
    .stTextInput>div>div>input { /* Text input styling */
        border-radius: 8px;
        border: 1px solid #FF69B4;
        padding: 10px;
    }
    .stTextArea>div>div>textarea { /* Text area styling */
        border-radius: 8px;
        border: 1px solid #FF69B4;
        padding: 10px;
    }
    .card {{
        background-color: white;
        border-radius: 15px;
        padding: 25px;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease-in-out;
    }}
    .card:hover {{
        transform: translateY(-5px);
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 24px;
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        white-space: pre-wrap;
        background-color: #F0F2F6;
        border-radius: 10px 10px 0 0;
        gap: 10px;
        padding-top: 10px;
        padding-bottom: 10px;
        border: 1px solid #FF69B4; /* Pembe kenarlık */
        color: #333333; /* Koyu metin */
    }}
    .stTabs [aria-selected="true"] {{
        background-color: #FF69B4; /* Seçili sekme pembe */
        color: white; /* Seçili sekme metni beyaz */
        border-bottom: none;
    }}
</style>
""", unsafe_allow_html=True)

# --- Helper function to parse recipe details from Markdown text ---
def parse_recipe_details(recipe_markdown: str) -> Dict[str, str]:
    """
    Parses key details from the recipe markdown string using regex.
    """
    details = {
        "tarif_adi": "Bilinmeyen Tarif",
        "malzemeler": "Malzemeler bulunamadı.",
        "kalori": "Bilinmiyor",
        "diyet_tipi": "Standart",
        "hazirlik_suresi": "Bilinmiyor",
        "pisirme_suresi": "Bilinmiyor",
        "porsiyon": "Bilinmiyor"
    }

    # Tarif Adı
    name_match = re.search(r"\*\*Tarif Adı:\*\* (.+)", recipe_markdown)
    if name_match:
        details["tarif_adi"] = name_match.group(1).strip()

    # Diyet Tipi (Genellikle üst başlıktan alınır)
    diet_type_match = re.search(r"### (.+) Diyeti İçin Tarif Önerisi", recipe_markdown)
    if diet_type_match:
        details["diyet_tipi"] = diet_type_match.group(1).strip()
    
    # Kalori
    calorie_match = re.search(r"Kalori:\s*\[?(\d+)\s*kcal", recipe_markdown)
    if calorie_match:
        details["kalori"] = calorie_match.group(1).strip()

    # Malzemeler (Yapılışı kısmına kadar olan tüm malzeme listesi)
    ingredients_match = re.search(r"\*\*Malzemeler:\*\*(.+?)\*\*Yapılışı:\*\*", recipe_markdown, re.DOTALL)
    if ingredients_match:
        details["malzemeler"] = ingredients_match.group(1).strip()
    
    # Hazırlık Süresi
    prep_time_match = re.search(r"\*\*Hazırlık Süresi:\*\* (.+)", recipe_markdown)
    if prep_time_match:
        details["hazirlik_suresi"] = prep_time_match.group(1).strip()

    # Pişirme Süresi
    cook_time_match = re.search(r"\*\*Pişirme Süresi:\*\* (.+)", recipe_markdown)
    if cook_time_match:
        details["pisirme_suresi"] = cook_time_match.group(1).strip()

    # Porsiyon
    portion_match = re.search(r"\*\*Porsiyon:\*\* (.+)", recipe_markdown)
    if portion_match:
        details["porsiyon"] = portion_match.group(1).strip()

    return details

# --- Main Application Logic ---

st.title("SmartMeal AI 🎯 Kişisel Diyet ve Tarif Asistanı")
st.write("""
Merhaba! SmartMeal AI, diyet türünüze, kalori hedefinize ve evdeki malzemelerinize göre kişiselleştirilmiş yemek tarifleri sunarak sağlıklı ve dengeli beslenmenizi kolaylaştırır.
""")

# Gemini API Anahtarı Yapılandırması
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    st.error("Google API Anahtarı bulunamadı. Lütfen `GOOGLE_API_KEY` ortam değişkenini ayarlayın veya Streamlit secrets kullanın.")

# --- Login/Register Logic ---
if not st.session_state.logged_in:
    st.subheader("Giriş Yap veya Kaydol")
    tab_login, tab_register = st.tabs(["Giriş Yap", "Kaydol"])

    with tab_login:
        st.write("#### Giriş Yap")
        login_email = st.text_input("E-posta", key="login_email")
        login_password = st.text_input("Şifre", type="password", key="login_password")
        if st.button("Giriş Yap", key="login_button"):
            if login_email.strip() == "" or login_password.strip() == "":
                st.error("Lütfen e-posta ve şifreyi girin.")
            else:
                try:
                    response = requests.post(f"{BACKEND_URL}/api/auth/login", json={"email": login_email, "password": login_password})
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.logged_in = True
                        st.session_state.user_info = {"email": login_email, "name": data.get("display_name"), "uid": data.get("user_id"), "token": data.get("token")}
                        # Reset the fetched flag so recipes are fetched again
                        if "user_recipes_fetched" in st.session_state:
                            del st.session_state.user_recipes_fetched
                        st.success("Giriş başarılı! Yönlendiriliyorsunuz...")
                        st.rerun()
                    else:
                        st.error(f"Giriş başarısız: {response.json().get('message', 'Bilinmeyen hata')}")
                except requests.exceptions.ConnectionError:
                    st.error("Backend sunucusuna bağlanılamadı. Lütfen sunucunun çalıştığından emin olun.")
                except Exception as e:
                    st.error(f"Bir hata oluştu: {e}")

    with tab_register:
        st.write("#### Kaydol")
        register_name = st.text_input("İsim Soyisim", key="register_name")
        register_email = st.text_input("E-posta", key="register_email")
        register_password = st.text_input("Şifre", type="password", key="register_password")
        if st.button("Kaydol", key="register_button"):
            if not register_name.strip() or not register_email.strip() or not register_password.strip():
                st.error("Lütfen tüm alanları doldurun.")
            else:
                try:
                    response = requests.post(f"{BACKEND_URL}/api/auth/register", json={
                        "email": register_email,
                        "password": register_password,
                        "name": register_name
                    })
                    if response.status_code == 201:
                        st.success("Kayıt başarılı! Giriş yapılıyor...")
                        # Doğrudan giriş yapmaya çalış
                        login_response = requests.post(f"{BACKEND_URL}/api/auth/login", json={
                            "email": register_email,
                            "password": register_password
                        })
                        if login_response.status_code == 200:
                            data = login_response.json()
                            st.session_state.logged_in = True
                            st.session_state.user_info = {"email": register_email, "name": data.get("display_name"), "uid": data.get("user_id"), "token": data.get("token")}
                            st.rerun()
                        else:
                            st.error(f"Kayıt sonrası otomatik giriş başarısız: {login_response.json().get('message', 'Bilinmeyen hata')}")
                    else:
                        st.error(f"Kayıt başarısız: {response.json().get('message', 'Bilinmeyen hata')}")
                except requests.exceptions.ConnectionError:
                    st.error("Backend sunucusuna bağlanılamadı. Lütfen sunucunun çalıştığından emin olun.")
                except Exception as e:
                    st.error(f"Bir hata oluştu: {e}")
else: # User is logged in
    # --- Sidebar: User Info and Navigation ---
    with st.sidebar:
        st.write(f"Merhaba, {st.session_state.user_info.get('name', 'Kullanıcı')} 👋")
        st.markdown("---") # Ayırıcı
        
        # Sidebar Navigasyon Butonları
        if st.button("Tarif Üret 🍳", key="nav_generate_recipe"):
            st.session_state.current_main_view = "recipe_generation"
            st.rerun()
        
        if st.button("💖 Beğenilen Tarifler", key="nav_liked_recipes"):
            st.session_state.current_main_view = "liked_recipes_list"
            st.rerun()

        st.markdown("---") # Ayırıcı
        if st.button("Çıkış Yap 🚪", key="logout_button"):
            st.session_state.logged_in = False
            st.session_state.user_info = {}
            st.session_state.generated_recipe_text = "" # Çıkışta temizle
            st.session_state.last_generated_recipe_details = None # Çıkışta temizle
            st.session_state.liked_recipes = [] # Çıkışta temizle
            if 'selected_liked_recipe' in st.session_state:
                del st.session_state.selected_liked_recipe
            if 'user_recipes_fetched' in st.session_state:
                del st.session_state.user_recipes_fetched
            st.session_state.current_main_view = "recipe_generation" # Ana görünümü sıfırla
            st.rerun()

    # Fetch liked recipes from backend if logged in and not already fetched
    if st.session_state.logged_in and "user_recipes_fetched" not in st.session_state:
        user_id = st.session_state.user_info.get("uid")
        token = st.session_state.user_info.get("token")
        if user_id and token:
            headers = {"x-access-token": token}
            try:
                response = requests.get(f"{BACKEND_URL}/api/recipes/user/{user_id}", headers=headers)
                if response.status_code == 200:
                    recipes_data = response.json()
                    # Her tarife id'nin dahil olduğundan emin ol
                    for recipe in recipes_data:
                        if 'id' not in recipe:
                            st.warning(f"Tarif '{recipe.get('tarif_adi', 'Bilinmeyen')}' için ID bulunamadı.")
                    st.session_state.liked_recipes = recipes_data
                    st.session_state.user_recipes_fetched = True # Tariflerin çekildiğini işaretle
                else:
                    st.error(f"Tarifler getirilirken hata: {response.json().get('message', 'Bilinmeyen hata')}")
            except requests.exceptions.ConnectionError:
                st.error("Backend sunucusuna bağlanılamadı. Lütfen sunucunun çalıştığından emin olun.")
            except Exception as e:
                st.error(f"Bir hata oluştu: {e}")

    # --- Main Content Area based on sidebar selection ---
    if st.session_state.current_main_view == "recipe_generation":
        # "Tarif Üret" görünümü: Tarif Ayarları ve Tarif Önerileri
        st.header("⚙️ Tarif Ayarları") # Tarif Ayarları ana ekranda
        col_diet, col_calorie = st.columns(2)
        with col_diet:
            diet_type: str = st.selectbox(
                "Diyet Tercihiniz:",
                ["Normal", "Vegan", "Vejetaryen", "Ketojenik", "Glutensiz", "Akdeniz", "Paleo", "Standart"],
                help="Hangi diyet türünü uyguluyorsunuz?",
                index=0, # Varsayılan olarak "Normal" seçili gelsin
                key="diet_type_select_main" # Key'i güncelledik
            )
        with col_calorie:
            calorie_goal: int = st.number_input(
            "Günlük Kalori Hedefiniz (kcal):",
            min_value=500,
            max_value=5000,
            value=2000,
            step=100,
            help="Günlük almayı hedeflediğiniz kalori miktarı."
        )
        ingredients: str = st.text_area(
            "Evdeki Mevcut Malzemeleriniz (virgülle ayırın):",
            placeholder="Örn: tavuk göğsü, brokoli, pirinç, soğan",
            help="Mevcut malzemelerinizi girerek size özel tarifler alabilirsiniz.",
            key="ingredients_text_area_main" # Key'i güncelledik
        )
        generate_recipe_button = st.button("Tarif Oluştur 🚀", key="generate_recipe_button_main")

        st.markdown("---") # Ayıraç

        # Tarif çıktısı alanı
        st.subheader("🍽️ Tarif Önerileri")
        col1, col2 = st.columns([1, 2]) # Sütunları burada tanımla

        if generate_recipe_button:
            if not GOOGLE_API_KEY:
                st.error("Tarif oluşturmak için Google API Anahtarı gereklidir.")
            elif not ingredients.strip():
                st.warning("Lütfen evdeki mevcut malzemeleri girin.")
            else:
                with st.spinner("🚀 Tarifiniz Oluşturuluyor..."):
                    try:
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        prompt = f"""
                        Bir diyet ve yemek tarifi asistanı olarak, aşağıdaki bilgilere göre kişiselleştirilmiş bir yemek tarifi oluşturun:

                        Diyet Tipi: {diet_type}
                        Kalori Hedefi: Yaklaşık {calorie_goal} kcal
                        Mevcut Malzemeler: {ingredients}

                        Tarif aşağıdaki Markdown formatında olmalıdır:
                        ### {diet_type} Diyeti İçin Tarif Önerisi
                        #### {calorie_goal} kcal Kalori Hedefine Uygun

                        **Tarif Adı:** [Tarif Adı]
                        **Açıklama:** [Kısa Açıklama]
                        **Hazırlık Süresi:** [Örn: 20 dakika]
                        **Pişirme Süresi:** [Örn: 30 dakika]
                        **Porsiyon:** [Örn: 2 kişilik]

                        **Malzemeler:**
                        - [Malzeme 1]
                        - [Malzeme 2]
                        - ...

                        **Yapılışı:**
                        1. [Adım 1]
                        2. [Adım 2]
                        ...

                        **Besin Değerleri (Tahmini):**
                        - Kalori: [Tahmini Kalori] kcal
                        - Protein: [Tahmini Protein] g
                        - Karbonhidrat: [Tahmini Karbonhidrat] g
                        - Yağ: [Tahmini Yağ] g

                        Lütfen bu formatın dışına çıkmayın.
                        """
                        response = model.generate_content(prompt)
                        st.session_state.generated_recipe_text = response.text
                        st.session_state.last_generated_recipe_details = parse_recipe_details(response.text) # Son tarifi detaylarıyla kaydet

                        with col1:
                            st.empty() # Görsel için yer tutucu

                        with col2:
                            st.markdown(f'<div class="recipe-card">{st.session_state.generated_recipe_text}</div>', unsafe_allow_html=True)
                            
                            # 'Beğen' butonu sadece bir tarif üretildiyse ve kullanıcı giriş yapmışsa gözükür
                            if st.session_state.generated_recipe_text and st.session_state.logged_in:
                                if st.button("❤️ Beğen", key="like_generated_recipe_button"):
                                    new_liked_recipe = {
                                        "tarif_adi": st.session_state.last_generated_recipe_details["tarif_adi"],
                                        "malzemeler": st.session_state.last_generated_recipe_details["malzemeler"],
                                        "kalori": st.session_state.last_generated_recipe_details["kalori"],
                                        "tarih": str(date.today()),
                                        "diyet_tipi": st.session_state.last_generated_recipe_details["diyet_tipi"],
                                        "full_recipe_markdown": st.session_state.generated_recipe_text,
                                        "hazirlik_suresi": st.session_state.last_generated_recipe_details.get("hazirlik_suresi"),
                                        "pisirme_suresi": st.session_state.last_generated_recipe_details.get("pisirme_suresi"),
                                        "porsiyon": st.session_state.last_generated_recipe_details.get("porsiyon")
                                    }

                                    # Check for duplicates before adding locally
                                    if not any(recipe["full_recipe_markdown"] == new_liked_recipe["full_recipe_markdown"] for recipe in st.session_state.liked_recipes):
                                        try:
                                            token = st.session_state.user_info.get("token")
                                            headers = {"x-access-token": token}
                                            save_response = requests.post(f"{BACKEND_URL}/api/recipes/save", json=new_liked_recipe, headers=headers)
                                            if save_response.status_code == 201:
                                                # Backend'den dönen response'dan recipe_id'yi al
                                                saved_recipe_data = save_response.json()
                                                recipe_id = saved_recipe_data.get("recipe_id")
                                                
                                                # Tarife ID'yi ekle
                                                new_liked_recipe["id"] = recipe_id
                                                st.session_state.liked_recipes.append(new_liked_recipe)
                                                st.success("Tarif beğenilenlere eklendi! ❤️")
                                                st.rerun()
                                            else:
                                                st.error(f"Tarif kaydedilirken hata: {save_response.json().get('message', 'Bilinmeyen hata')}")
                                        except requests.exceptions.ConnectionError:
                                            st.error("Backend sunucusuna bağlanılamadı. Lütfen sunucunun çalıştığından emin olun.")
                                        except Exception as e:
                                            st.error(f"Bir hata oluştu: {e}")
                                    else:
                                        st.info("Bu tarif zaten beğenilenler listenizde.")
                                    

                    except Exception as e:
                        st.error(f"Tarif oluşturulurken bir hata oluştu: {e}")
                        with col2:
                            st.markdown(
                                f'<div class="recipe-card" style="background-color: #ffe0e0; border: 1px solid #ff9999; color: #cc0000;">'
                                f'<h3>Hata! 😢</h3>'
                                f'<p>Tarif oluşturulurken bir sorun yaşandı. Lütfen daha sonra tekrar deneyin veya '
                                f'girdiğiniz bilgileri kontrol edin.</p>'
                                f'<p>Hata Detayı: {e}</p>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
        elif st.session_state.generated_recipe_text: # Daha önce üretilmiş bir tarif varsa göster
            with col1:
                st.empty()
            with col2:
                st.markdown(f'<div class="recipe-card">{st.session_state.generated_recipe_text}</div>', unsafe_allow_html=True)
                if st.session_state.logged_in:
                    if st.button("❤️ Beğen", key="like_reloaded_recipe_button"):
                        new_liked_recipe = {
                            "tarif_adi": st.session_state.last_generated_recipe_details["tarif_adi"],
                            "malzemeler": st.session_state.last_generated_recipe_details["malzemeler"],
                            "kalori": st.session_state.last_generated_recipe_details["kalori"],
                            "tarih": str(date.today()),
                            "diyet_tipi": st.session_state.last_generated_recipe_details["diyet_tipi"],
                            "full_recipe_markdown": st.session_state.generated_recipe_text,
                            "hazirlik_suresi": st.session_state.last_generated_recipe_details.get("hazirlik_suresi"),
                            "pisirme_suresi": st.session_state.last_generated_recipe_details.get("pisirme_suresi"),
                            "porsiyon": st.session_state.last_generated_recipe_details.get("porsiyon")
                        }
                        if not any(recipe["full_recipe_markdown"] == new_liked_recipe["full_recipe_markdown"] for recipe in st.session_state.liked_recipes):
                            try:
                                token = st.session_state.user_info.get("token")
                                headers = {"x-access-token": token}
                                save_response = requests.post(f"{BACKEND_URL}/api/recipes/save", json=new_liked_recipe, headers=headers)
                                if save_response.status_code == 201:
                                    # Backend'den dönen response'dan recipe_id'yi al
                                    saved_recipe_data = save_response.json()
                                    recipe_id = saved_recipe_data.get("recipe_id")
                                    
                                    # Tarife ID'yi ekle
                                    new_liked_recipe["id"] = recipe_id
                                    st.session_state.liked_recipes.append(new_liked_recipe)
                                    st.success("Tarif beğenilenlere eklendi! ❤️")
                                    st.rerun()
                                else:
                                    st.error(f"Tarif kaydedilirken hata: {save_response.json().get('message', 'Bilinmeyen hata')}")
                            except requests.exceptions.ConnectionError:
                                st.error("Backend sunucusuna bağlanılamadı. Lütfen sunucunun çalıştığından emin olun.")
                            except Exception as e:
                                st.error(f"Bir hata oluştu: {e}")
                        else:
                            st.info("Bu tarif zaten beğenilenler listenizde.")
        else: # Hiçbir tarif üretilmediyse veya sayfa yenilendiyse başlangıç mesajı
            with col1:
                st.empty()
            
    
    elif st.session_state.current_main_view == "liked_recipes_list":
        # "Beğenilen Tarifler" listesi görünümü
        st.subheader("💖 Beğenilen Tarifler")
        if not st.session_state.liked_recipes:
            st.info("Henüz beğenilen bir tarifiniz yok. 'Tarif Üret' bölümünden tarif oluşturup beğenebilirsiniz! 😊")
        else:
            for i, recipe in enumerate(st.session_state.liked_recipes):
                with st.container(): # Görsel gruplama için st.container kullan
                    st.markdown(f'<div class="recipe-card">', unsafe_allow_html=True)
                    st.markdown(f"**Tarif Adı:** {recipe['tarif_adi']}")
                    st.markdown(f"**Diyet Tipi:** {recipe['diyet_tipi']}")
                    st.markdown(f"**Kalori:** {recipe['kalori']} kcal")
                    st.markdown(f"**Hazırlık Süresi:** {recipe.get('hazirlik_suresi', 'N/A')}") # Hazırlık süresi eklendi
                    st.markdown(f"**Pişirme Süresi:** {recipe.get('pisirme_suresi', 'N/A')}") # Pişirme süresi eklendi
                    st.markdown(f"**Porsiyon:** {recipe.get('porsiyon', 'N/A')}") # Porsiyon eklendi
                    st.markdown(f"**Malzemeler:** {recipe['malzemeler']}") # Tüm malzemeler string olarak gösterildi
                    st.markdown(f"**Tarih:** {recipe['tarih']}")
                    # Tarife genel bakış ve kaldırma butonu
                    col_view, col_remove = st.columns([1, 1])
                    with col_view:
                        if st.button(f"Tarifi Görüntüle 📖", key=f"view_liked_recipe_{i}"):
                            st.session_state.selected_liked_recipe = recipe
                            st.session_state.current_main_view = "liked_recipe_detail"
                            st.rerun()
                    with col_remove:
                        if st.button(f"Kaldır 🗑️", key=f"remove_liked_recipe_{i}"):
                            # ID kontrolü ekle
                            if 'id' not in recipe:
                                st.error("Bu tarif için ID bulunamadı. Lütfen sayfayı yenileyin.")
                                continue
                            
                            try:
                                token = st.session_state.user_info.get("token")
                                user_id = st.session_state.user_info.get("uid")
                                recipe_id_to_delete = recipe['id'] # Backend'den gelen 'id' alanı
                                headers = {"x-access-token": token}
                                delete_response = requests.delete(f"{BACKEND_URL}/api/recipes/{recipe_id_to_delete}", headers=headers)
                                if delete_response.status_code == 200:
                                    st.session_state.liked_recipes.pop(i)
                                    st.success("Tarif beğenilenlerden kaldırıldı!")
                                    st.rerun()
                                else:
                                    st.error(f"Tarif silinirken hata: {delete_response.json().get('message', 'Bilinmeyen hata')}")
                            except requests.exceptions.ConnectionError:
                                st.error("Backend sunucusuna bağlanılamadı. Lütfen sunucunun çalıştığından emin olun.")
                            except Exception as e:
                                st.error(f"Bir hata oluştu: {e}")
                    st.markdown('</div>', unsafe_allow_html=True) # Tarif kartı div'ini kapat

    elif st.session_state.current_main_view == "liked_recipe_detail":
        # "Kayıtlı Tarif Detayı" görünümü
        st.subheader("💖 Seçilen Beğenilen Tarif")
        if 'selected_liked_recipe' in st.session_state and st.session_state.selected_liked_recipe:
            recipe = st.session_state.selected_liked_recipe
            st.markdown(f'<div class="recipe-card">', unsafe_allow_html=True)
            st.markdown(f"**Tarif Adı:** {recipe['tarif_adi']}")
            st.markdown(f"**Diyet Tipi:** {recipe['diyet_tipi']}")
            st.markdown(f"**Kalori:** {recipe['kalori']} kcal")
            st.markdown(f"**Hazırlık Süresi:** {recipe.get('hazirlik_suresi', 'N/A')}")
            st.markdown(f"**Pişirme Süresi:** {recipe.get('pisirme_suresi', 'N/A')}")
            st.markdown(f"**Porsiyon:** {recipe.get('porsiyon', 'N/A')}")
            st.markdown(f"**Malzemeler:** {recipe['malzemeler']}")
            st.markdown(f"**Tarih:** {recipe['tarih']}")
            st.markdown("---")
            st.subheader("Detaylı Tarif:")
            st.markdown(recipe["full_recipe_markdown"])
            st.markdown('</div>', unsafe_allow_html=True)

            col_detail_actions = st.columns(2)
            with col_detail_actions[0]:
                if st.button("⬅️ Geri Dön", key="back_to_main_from_detail"):
                    st.session_state.current_main_view = "liked_recipes_list" # Listeye geri dön
                    if 'selected_liked_recipe' in st.session_state:
                        del st.session_state.selected_liked_recipe
                    st.rerun()
            with col_detail_actions[1]:
                if st.button("Kaldır 🗑️", key=f"remove_from_detail_{recipe['tarif_adi']}"):
                    # ID kontrolü ekle
                    if 'id' not in recipe:
                        st.error("Bu tarif için ID bulunamadı. Lütfen sayfayı yenileyin.")
                    else:
                        try:
                            token = st.session_state.user_info.get("token")
                            user_id = st.session_state.user_info.get("uid")
                            recipe_id_to_delete = recipe['id']
                            headers = {"x-access-token": token}
                            delete_response = requests.delete(f"{BACKEND_URL}/api/recipes/{recipe_id_to_delete}", headers=headers)
                            if delete_response.status_code == 200:
                                # liked_recipes listesinden tarifi kaldır
                                st.session_state.liked_recipes = [lr for lr in st.session_state.liked_recipes if lr.get('id') != recipe_id_to_delete]
                                st.success("Tarif beğenilenlerden kaldırıldı!")
                                st.session_state.current_main_view = "liked_recipes_list" # Listeye geri dön
                                if 'selected_liked_recipe' in st.session_state:
                                    del st.session_state.selected_liked_recipe
                                st.rerun()
                            else:
                                st.error(f"Tarif silinirken hata: {delete_response.json().get('message', 'Bilinmeyen hata')}")
                        except requests.exceptions.ConnectionError:
                            st.error("Backend sunucusuna bağlanılamadı. Lütfen sunucunun çalıştığından emin olun.")
                        except Exception as e:
                            st.error(f"Bir hata oluştu: {e}")

        else:
            st.info("Görüntülenecek seçili bir tarif bulunamadı.")