from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt

# Bcrypt algoritmasını kullanarak şifreleme motorunu tanımlıyoruz
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "9985caaa4f9fb6026070c83e07ba05a3536568c6baea34348cdc612a2a3f234b"
ALGORITHM = "HS256"

# 1. Düz şifreyi alıp tanınmaz hale getiren fonksiyon
def hash_password(password:str) -> str:
    return pwd_context.hash(password)

# 2. Kullanıcı giriş yaparken girdi dökülen şifre ile veritabanındaki gizli şifreyi karşılaştıran fonksiyon
def verify_password(plain_password:str, hashed_password:str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# 3. Kullanıcıya JWT giriş kartı üreten fonksiyon
def create_access_token(data: dict):
    to_encode = data.copy() 
    #Gelen kullanıcı bilgilerinin bir kopyasını alıyoruz

    expire = datetime.utcnow() + timedelta(minutes=30)
    #Kartın son kullanma vaktini şu andan 30 dakika sonrası olarak hesaplıyoruz

    to_encode.update({"exp": expire})
    #Bu son kullanma vaktini kartın içine "exp" (expiration) adıyla ekliyoruz

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    #jwt kütüphanesini kullanarak bilgileri gizli anahtarımız ve algoritmamızla mühürlüyoruz

    return encoded_jwt
    #Üretilen upuzun, şifreli metni (token'ı) geri döndürüyoruz

def decode_access_token(token: str):
    try:
        # jwt kütüphanesi kartı bizim SECRET_KEY ile açıp çözmeye çalışıyor
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Kartın içinden bilgileri çekiyoruz
        username: str = payload.get("username") 
        user_id: str = payload.get("user_id")

        # Eğer kartın içinde bu bilgiler yoksa geçersiz sayıyoruz
        if username is None or user_id is None:
            return None
        
        # Bilgiler tam ve doğruysa döndürüyoruz
        return {"user_id": user_id, "username": username}
    
    except jwt.PyJWTError:
        return None