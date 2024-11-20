from sqlmodel import Field, Session, SQLModel, create_engine
from typing import Optional

class Messages(SQLModel, table=True):
  id: Optional[int] = Field(default=None, primary_key=True)
  chat_id: Optional[int]
  role: str
  content: str

msg = Messages(role='user', content='Gradient Descent Algorithm')

URL_DATABASE = 'postgresql://postgres:140817@localhost:5432/agent'
engine = create_engine(URL_DATABASE)
SQLModel.metadata.create_all(engine)