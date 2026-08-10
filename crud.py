from sqlmodel import Session, select
from database import engine
from models import User, Expense 
from security import hash_password
from sqlmodel import func
from datetime import datetime, timedelta

def create_user(username:str, email:str, password:str):

    # 1. Session (oturum) tünelini motorumuzu kullanarak açtık
    with Session(engine) as session:
        try:
            hashed_pw = hash_password(password)
            # 2. Gelen düz şifreyi burada hashliyoruz

            new_user = User(userName=username, email=email, hashed_password=hashed_pw)
            # 3. models.py'daki User sınıfından yeni bir Python nesnesi ürettik

            session.add(new_user)
            # 4. Bu nesneyi veritabanı tüneline (kuyruğa) ekledik

            session.commit()
            # 5. Kuyruktaki işlemi veritabanına kalıcı olarak işliyoruz (Commit)

            session.refresh(new_user)
            # 6. MySQL'in bu kullanıcıya verdiği otomatik id'yi Python nesnemize geri yüklüyoruz

            return new_user
            # 7. Oluşan kullanıcının son halini fonksiyonun çağrıldığı yere dönüyoruz
        except Exception as e:
            print("Veritabanı Hatası: {e}")
            raise e


def create_expense(title:str, amount:float, category:str, user_id:int, date: str = None):
    with Session(engine) as session:
        # Expense sınıfından yeni bir harcama nesnesi oluşturuyoruz
        new_expense = Expense(
            title=title,
            amount=amount,
            category=category,
            user_id=user_id)

        new_expense = Expense(title=title, 
            amount=amount, 
            category=category, 
            user_id=user_id, 
            date=date)

        session.add(new_expense)
        session.commit()
        session.refresh(new_expense)
        return new_expense
    

def get_all_users():
    with Session(engine) as session:
        # 1. SQLModel'e "Kullanıcı tablosundaki her şeyi seç" diyoruz
        statement = select(User)
        
        # 2. Bu isteği veritabanına gönderip sonuçları listeliyoruz
        results = session.exec(statement).all()
        return results


def get_user_expenses(user_id: int):
    with Session(engine) as session:
        # Önce veritabanından o id'ye sahip kullanıcıyı buluyoruz
        user = session.get(User, user_id)
        if user:
            return user.expenses
        return[]
    

def get_user_by_username(username:str):
    with Session(engine) as session:
        statement = select(User).where(User.userName == username)
        return session.exec(statement).first() #Bulursa kullanıcıyı, bulamazsa none döndürcek


# Giriş yapmış kullanıcının harcamalarını getiren fonk
def get_current_user_expenses(user_id: int):
    #expense tablosundan sadece bu user_id'ye ait olanları filtreleyip getiriyoruz
    with Session(engine) as session: 
        statement = select(Expense).where(Expense.user_id == user_id)
        results = session.exec(statement)
        return results.all()


# Belirli bir haarcamayı silen fonk
def delete_expense(expense_id: int, user_id: int):
    # Güvenlik önlemi: Harcamayı ararken hem ID'sine hem de istek atan kullanıcının ID'sine bakıyoruz
    with Session(engine) as session: 
        statement = select(Expense).where(Expense.id == expense_id, Expense.user_id == user_id)
        expense = session.exec(statement).first()

        if expense:
            session.delete(expense)
            session.commit()
            return True
        return False
    
# Belirli bir harcamayı güncelleyen fonk
def update_expense(expense_id: int, user_id: int, title: str, amount: float, category: str):
    with Session(engine) as session:
        # Sadece harcamanın sahibi güncelleyebilsin diye filtreliyoruz
        statement = select(Expense).where(Expense.id == expense_id, Expense.user_id == user_id)
        expense = session.exec(statement).first()

        if expense:
            expense.title =title
            expense.amount = amount
            expense.category = category
            session.add(expense)
            session.commit()
            session.refresh(expense)
            return expense
        return None
    

# Veritabanında kategori bazlı toplama işlemi yapacak fonksiyon
def get_expense_summary_by_category(user_id: int):
    with Session(engine) as session:
        # Kategorileri gruplayıp, her kategorinin toplam harcama miktarını hesaplıyoruz
        statement = (
            select(Expense.category, func.sum(Expense.amount).label("total_amount"))
            .where(Expense.user_id == user_id)
            .group_by(Expense.category)
        )
        results = session.exec(statement).all()
        summary = {category : total for category, total in results}
        return summary
    

# Son 30 günün harcamalarını çeken fonksiyon
def get_recent_expenses(user_id: int, days: int = 30):
    with Session(engine) as session:
        #Şuanki tarihten 30 gün öncekini çıkarıtoyruz
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        #Harcama tarihi 30 gün öncekinden büyük veya eşit olsun
        statement = select(Expense).where(
            Expense.user_id == user_id,
            Expense.date >= cutoff_date 
        )
        return session.exec(statement).all()