import os
from dotenv import load_dotenv
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool
from langchain_google_community import GoogleSearchAPIWrapper
from langchain.agents import create_tool_calling_agent
from langchain.agents import AgentExecutor
from langchain_core.prompts.chat import MessagesPlaceholder
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_community.callbacks import StreamlitCallbackHandler
from main import Messages, start_db
from sqlmodel import Session, select
from sqlalchemy.sql import func

load_dotenv('.env')

google_api_key = os.getenv('GOOGLE_CSE_API_KEY')
search_engine = os.getenv('SEARCH_ENGINE_ID')
openai_api_key = os.getenv('CHAT_GPT_API_KEY')

os.environ["GOOGLE_CSE_ID"] = search_engine
os.environ["GOOGLE_API_KEY"] = google_api_key

search = GoogleSearchAPIWrapper()

google_tool = Tool(
  name="google_search",
  description="Search Google for recent results.",
  func=search.run,
)

def store_data(engine, chat_id, prompt, response):
  with Session(engine) as session:
    data = Messages(chat_id=chat_id, prompt=prompt, response=response)
    session.add(data)
    session.commit()
    
def load_session_data(engine, chat_id):
  with Session(engine) as session:
    result = session.exec(select(Messages).where(Messages.chat_id == chat_id)).all()

    return result

def main():  
  llm = ChatOpenAI(openai_api_key=openai_api_key, temperature=0.9)
  system_prompt = 'Compelete this task'

  prompt_template = ChatPromptTemplate.from_messages(
    [
      ("system", system_prompt),
      MessagesPlaceholder("chat_history", optional=True),
      ("human", "{input}"),
      MessagesPlaceholder("agent_scratchpad"),
    ]
  )
    
  agent = create_tool_calling_agent(llm, [google_tool], prompt_template)
  agent_executor = AgentExecutor(agent=agent, tools=[google_tool])
  engine = start_db()
  
  st.title("💬 ChatBot")
      
  with Session(engine) as session:
    chat_id = session.exec(select(func.max(Messages.chat_id))).one()
  
  if chat_id == None:
    chat_id = 0
    st.chat_message('assistant').write("How can I help you?")
  
  else:
    session_data = load_session_data(engine=engine, chat_id=chat_id)
    
    for msg in session_data:
      st.chat_message('user').write(msg.prompt)
      st.chat_message('assistant').write(msg.response)
              
  if user_prompt := st.chat_input(placeholder='Your message'):
    st_callback = StreamlitCallbackHandler(st.container())
    response = agent_executor.invoke({'input': user_prompt}, {"callbacks": [st_callback]})
    response = response['output']
    
    st.chat_message('user').write(user_prompt)
    st.chat_message('assistant').write(response)
    store_data(engine=engine, chat_id=chat_id, prompt=user_prompt, response=response)
  
  # if "messages" not in st.session_state:
  #   st.session_state["messages"] = [
  #     {"role": "assistant", "content": "Hi, I'm a blogbot who can make blog for any theme. How can I help you?"}
  #   ]
  
  # for msg in st.session_state.messages:
  #   st.chat_message(msg["role"]).write(msg["content"])
    
  # if prompt := st.chat_input(placeholder='Gradient Descent Algorithm'):
  #   st.session_state.messages.append({
  #     'role': 'user', 'content': prompt
  #   })
  #   st.chat_message('user').write(prompt)
    
  #   with st.chat_message('assistant'):
  #     st_callback = StreamlitCallbackHandler(st.container())
  #     blog = agent_executor.invoke({'input': 'Find' + prompt}, {"callbacks": [st_callback]})
  #     blog = blog['output']
  #     slogan = llm.invoke(f'Highlight the main essence of this text into a slogan: {blog}')
  #     blog = f'{slogan.content}\n\n{blog}'
  #     st.session_state.messages.append({"role": "assistant", "content": blog})
  #     st.write(blog)
  
if __name__ == '__main__':
  main()