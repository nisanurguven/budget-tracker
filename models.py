from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from datetime import datetime


# 1. Kullanıcı Tablosu
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    userName: str = Field(index=True, unique=True)
    email: str
    hashed_password: str #hasing şifreyi tutcağımız yer

    expenses: List["Expense"] = Relationship(back_populates="user")

# 2. Harcama Tablosu
class Expense(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    amount: float
    category: str
    date: Optional[str] = None

    # Yabancı Anahtar (Foreign Key): Bu harcama hangi kullanıcıya ait?
    user_id: int = Field(foreign_key="user.id") #user tablosunun id

    # İlişki: Bu harcamanın sahibi olan kullanıcı nesnesi
    user: User = Relationship(back_populates="expenses")  