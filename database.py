from sqlmodel import SQLModel, create_engine
from models import User, Expense # models.py dosyasından classları çağırıyoruz


DATABASE_URL = "mysql+pymysql://root:N1i4s8a6!@localhost:3306/budget_tracker"

engine = create_engine(DATABASE_URL) 
# echo=True sayesinde terminalde dönen SQL komutlarını canlı görebileceğiz.

def create_db_and_tables():
    # models.py dosyasındaki sınıfları MySQL'deki tablolara dönüştürür.
    SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    create_db_and_tables()
    print("Tablolar başarıyla oluşturuldu!")