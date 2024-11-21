from sqlmodel import Field, Session, SQLModel, create_engine
from typing import Optional

class Messages(SQLModel, table=True):
  id: Optional[int] = Field(default=None, primary_key=True)
  chat_id: Optional[int]
  prompt: str
  response: str

def start_db():
  URL_DATABASE = 'postgresql://postgres:140817@localhost:5432/agent'
  engine = create_engine(URL_DATABASE)
  SQLModel.metadata.create_all(engine)
  
  return engine

if __name__ == '__main__':
  engine = start_db()