import os
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool
from langchain_google_community import GoogleSearchAPIWrapper
from langchain.agents import create_tool_calling_agent
from langchain.agents import AgentExecutor
from langchain_core.prompts.chat import MessagesPlaceholder
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_community.agent_toolkits.load_tools import load_tools
import streamlit as st
from langchain_community.callbacks import StreamlitCallbackHandler

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

def create_banner(size, bgColor, message, font, fontColor):
  W, H = size
  banner = Image.new('RGB', size, bgColor)
  draw = ImageDraw.Draw(banner)
  _, _, w, h = draw.textbbox((0, 0), message, font=font)
  draw.text(((W-w)/2, (H-h)/2), message, font=font, fill=fontColor)
  
  return banner

def save_to_txt(text):
  with open('output/img_text.txt', 'w', encoding='utf-8') as file:
    file.write(text)
  
def main():
  llm = ChatOpenAI(openai_api_key=openai_api_key, temperature=0.9)
  system_prompt = 'Create clear blog from the following information provided in Russian without special characters. Divide it into paragraphs to highlight different subtopics'

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
  
  st.title("💬 BlogBot")
  
  if "messages" not in st.session_state:
    st.session_state["messages"] = [
      {"role": "assistant", "content": "Hi, I'm a blogbot who can make blog for any theme. How can I help you?"}
    ]
  
  for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])
    
  if prompt := st.chat_input(placeholder='Gradient Descent Algorithm'):
    st.session_state.messages.append({
      'role': 'user', 'content': prompt
    })
    st.chat_message('user').write(prompt)
    
    with st.chat_message('assistant'):
      st_callback = StreamlitCallbackHandler(st.container())
      response = agent_executor.invoke({'input': 'Найди' + prompt}, {"callbacks": [st_callback]})
      st.session_state.messages.append({"role": "assistant", "content": response})
      st.write(response['output'])
  
if __name__ == '__main__':
  main()