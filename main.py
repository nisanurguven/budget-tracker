from fastapi import FastAPI, HTTPException, status, Depends
from models import SQLModel, Expense
from security import verify_password, create_access_token, decode_access_token
import crud
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
import os 
from google import genai
from dotenv import load_dotenv
from database import engine
from google.genai import types

SQLModel.metadata.create_all(bind=engine)

# Yazdığımız FastAPI uygulamasını başlatıyoruz
app = FastAPI(title="Budget Tracker API", version="1.0")

# Kilit sistemini (OAuth2) tanımlıyoruz
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Geliştirme aşamasında tüm kökenlerden (localhost vb.) isteklere izin verir
    allow_credentials=True,
    allow_methods=["*"], # GET, POST, PUT, DELETE tüm isteklere izin ver
    allow_headers=["*"], # Authorization (Token) dahil tüm başlıklara izin ver
)


# Güvenlik görevlimizi buraya yerleştiriyoruz
def get_current_user(token:str = Depends(oauth2_scheme)):
    # Gelen token'ı çözmesi için security.py'daki decode motoruna gönderiyoruz
    user_data = decode_access_token(token)

    # Eğer token sahteyse, süresi bittiyse veya çözülemediyse hata fırlatıyoruz
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya süresi dolmuş giriş kartı!",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Her şey doğruysa, kartın içinden çözülen kullanıcı bilgilerini döndürüyoruz
    return user_data


#Ilk "Hoşgeldin" Endpoint'i (GET isteği)
@app.get("/")
def home():
    return {"message": "Harcama Takip Sistemi API'ına Hoş Geldiniz"}


# Tüm Kullanıcıları Getiren Endpoint
@app.get("/users")
def read_all_users():
    users = crud.get_all_users()
    return users


# Yeni Kullanıcı Oluşturan Endpoint 
@app.post("/users", tags=["Kullanıcı İşlemleri"], summary="Yeni Kullanıcı Kaydı")
def add_new_user(username:str, email:str, password:str):
    user = crud.create_user(username=username, email=email, password=password)
    return {
        "status": "Kullanıcı Ekleme Başarılı", 
        "data": {
            "id": user.id,
            "name": user.userName, 
            "email": user.email}}


# Yeni Harcama Oluşturan Endpoint 
@app.post("/expenses", tags=["Harcama Yönetimi"], summary="Harcama Ekleme")
def add_new_expense(
    title:str,
    amount:float,
    category:str,
    current_user = Depends(get_current_user),
    date: str = None
    ):

    #Giriş yapmış kullanıcının id'sini token üzerinden alıyoruz
    logged_in_user_id = current_user["user_id"]

    # Harcamayı bu ID ile oluşturuyoruz
    expense = crud.create_expense(
        title=title,
        amount=amount,
        category=category,
        user_id=logged_in_user_id,
        date=date
        )
    return {"status": "Harcama Ekleme Başarılı", "data": expense}


# Belirli bir Kullanıcının Harcamalarını Getirme Endpoint'i
@app.get("/users/{user_id}/expenses")
def read_user_expenses(user_id: int):
    expenses = crud.get_user_expenses(user_id=user_id)
    return expenses


#Kullanıcı Girişi
@app.post("/login", tags=["Kimlik Doğrulama"], summary="Giriş Yap ve Token Al")

# 1. Veritabanından bu kullanıcı adına sahip bir kullanıcı var mı diye bakıyoruz
def login(form_data: OAuth2PasswordRequestForm =Depends()): # <-- Form verisi olarak bekliyoruz
    # Formdan gelen kullanıcı adıyla veritabanında arama yapıyoruz
    user = crud.get_user_by_username(form_data.username)

    # 2. Kullanıcı yoksa veya şifre yanlışsa 401 Yetkisiz Hatası fırlatıyoruz
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya şifre hatalı!"
        )
    # 1. Kartın içine gizlenecek kullanıcı bilgilerini bir sözlük (dict) olarak hazırlıyoruz
    token_data = {"user_id": user.id, "username": user.userName}

    # 2. Hazırladığımız bu bilgileri security.py'daki motorumuza gönderip token üretiyoruz
    access_token = create_access_token(data=token_data)

    # 3. Kullanıcıya başarılı yanıtıyla birlikte ürettiğimiz bu kartı teslim ediyoruz
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "message": f"Hoş geldin {user.userName}! Giriş kartın başarıyla oluşturuldu."
    }


# Giriş yapmış kullanıcının kendisine ait harcalamaları listeleme
@app.get("/expenses", tags=["Harcama Yönetimi"], summary="Kullanıcının Kendi Harcamalarını Listele")
def read_my_expenses(current_user: dict = Depends(get_current_user)):
    logged_in_user_id = current_user["user_id"]
    expenses = crud.get_current_user_expenses(user_id=logged_in_user_id)
    return expenses


# İstatistik Kapısı
@app.get("/expenses/summary", tags=["Harcama Yönetimi"], summary="Kategori Bazlı Harcama İstatistikleri")
def read_expenses_summary(current_user: dict = Depends(get_current_user)):
    logged_in_user_id = current_user["user_id"]
    summary = crud.get_expense_summary_by_category(user_id=logged_in_user_id)
    return summary


# Harcama silme kapısı
@app.delete("/expenses/{expense_id}", tags=["Harcama Yönetimi"], summary="Harcama sil")
def remove_expenses(expense_id: int, current_user: dict = Depends(get_current_user)):
    logged_in_user_id = current_user["user_id"]
    success = crud.delete_expense(expense_id=expense_id, user_id=logged_in_user_id)

    if not success:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail="Harcama bulunmadı veya bu harcamayı silmeye yetkiniz yok!"
        )
    return {"status": "Harcama başarıyla silindi."}

# Harcama güncelleme kapısı
@app.put("/expenses/{expense_id}", tags=["Harcama Yönetimi"], summary="Harcama Güncelleme")
def edit_expense(
    expense_id: int,
    title: str,
    amount: float,
    category: str,
    current_user: dict = Depends(get_current_user)
):
    logged_in_user_id = current_user["user_id"]
    updated_expense = crud.update_expense(
        expense_id=expense_id,
        user_id=logged_in_user_id,
        title=title,
        amount=amount,
        category=category
    )

    if not updated_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Harcama bulunamadı veya bu harcamayı güncellemeye yetkiniz yok!"
        )
    return {"status": "Harcamanız başarıyla güncellendi.", "data":updated_expense}


# .env dosyasındaki değişkenleri yüklüyoruz
load_dotenv()

# Ortam değişkeninden API Key'i güvenle çekiyoruz
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# Eğer .env dosyasında anahtar yoksa uygulamanın çökmesini önlemek için kontrol
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY .env dosyasında bulunamadı!")


# API Key'i koda gömmüyoruz, sistem ortam değişkeninden otomatik okuyor:
client = genai.Client(api_key=GEMINI_API_KEY)

print("Gemini client oluşturuldu")


@app.post("/ai/advice", tags=["Yapay Zeka Danışmanı"], summary="Kullanıcıya Özel Yapay Zeka Tavsiyesi Al.")
def get_ai_financial_advice(current_user: dict = Depends(get_current_user)):
    logged_in_user_id = current_user["user_id"]

    # Son 30 gündeki harcamaları veritabanından çekiyoruz
    recent_expenses = crud.get_recent_expenses(user_id=logged_in_user_id, days=30)

    if not recent_expenses:
        return {"ai_advice": "You don't have any recorded expenses in the last 30 days yet!"}
    
    # Harcamaları USD ($) formatında metne dönüştürüyoruz
    expense_list_text = "\n".join([f"- {e.category}: ${e.amount:.2f} ({e.title})" for e in recent_expenses])

    prompt = f"""
    You are the official personal finance advisor for the "BudgetTracker" app.
    User's name: {current_user['username']}

    Here is the user's expense summary for the last 30 days:
    {expense_list_text}

    Rules:
    1. Greet the user by their name and use an encouraging, friendly, and professional tone.
    2. Identify the category with the highest spending and provide 1 practical savings tip.
    3. Keep your response under 3 sentences and under 100 words.
    4. CRITICAL: All monetary figures are strictly in USD ($). Never use TL, EUR, or any other currency symbol.
    """

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction="You are an expert personal financial analyst. You communicate strictly in English with a witty and professional tone."
            )
        )

        return {
            "status": "Başarılı",
            "ai_advice": response.text
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gemini API Error: {str(e)}"
        )