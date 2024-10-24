import requests
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import openai
import re
from PIL import Image, ImageDraw, ImageFont
from docx import Document

load_dotenv('.env')

google_api_key = os.getenv('GOOGLE_CSE_API_KEY')
search_engine = os.getenv('SEARCH_ENGINE_ID')
openai.api_key = os.getenv('CHAT_GPT_API_KEY')

import requests

def search_news(query):
  url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={google_api_key}&cx={search_engine}"
  response = requests.get(url).json()
  output = [item['link'] for item in response['items']]
    
  return output

def keep_russian_characters(text): #Drop all html things to save tokens for payload
  return re.sub(r'[^А-Яа-яЁё ]', '', text)

def scrape_html(links):
  scraped_data = ''
  
  for link in links:
      
    try:
      url = requests.get(link)
      htmltext = url.text
          
      if 'Access Denied' in htmltext:
        print(f'ACCESS DENIED FOR A LINK | {link}')
          
        continue
          
      else:
        print(f'SCRAPED SUCCESSFUL!      | {link}')
          
      soup = BeautifulSoup(htmltext, "html.parser")
      link_data = ''
      
      for element in soup.find_all(['p', 'h1', 'h2', 'h3']):
        prepared_el = keep_russian_characters(str(element))
        link_data += prepared_el
    
      if len(link_data) > 15000:
        link_data = link_data[:15000]
    
      scraped_data += link_data
      
    except requests.exceptions.Timeout:
      print(f'TIMEOUT ERROR FOR A LINK | {link}')
          
      continue
      
    except requests.exceptions.RequestException as e:
      print(f'ERROR FETCHING LINK       | {link} | {e}')
        
      continue
  
  if len(scraped_data) > 160000:
    scraped_data = scraped_data[:160000]
  
  return scraped_data

def chat_gpt(content, prompt):
  prompt = f"{prompt}\n\n{content}"
  response = openai.ChatCompletion.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
  )
  
  return response.choices[0].message['content'].strip()

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
  links = search_news('Важность раннего развития детей')
  content = scrape_html(links)
  
  #Generating blog using chatGPT
  blog_prompt = 'Highlight from this text the main point about the importance of early childhood development, format the resulting answer in the form of a blog in russian language without any special sings(like *, $ etc.).:'
  blog = chat_gpt(content, blog_prompt)
  document = Document()
  document.add_paragraph(blog)
  document.save('output/blog.docx')
  
  #Generating slogan using chatGPT
  slogan_prompt = 'The main idea or slogan that will be used to create an image (e.g. a banner or infographic) should be extracted from the text. The text should be concise and memorable without any special sings(like *, $ etc.).'
  slogan = chat_gpt(blog, slogan_prompt)
  
  #Making an image using PIL
  myFont = ImageFont.truetype('C:/Windows/Fonts/Arial.ttf', 30)
  myImage = create_banner((1000, 700), 'yellow', slogan, myFont, 'black')
  myImage.save('output/slogan_banner.png', 'PNG')
  
  # Writing slogan text to txt file
  save_to_txt(slogan)
  
if __name__ == '__main__':
  main()