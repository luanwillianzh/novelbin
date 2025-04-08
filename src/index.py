import requests
from bs4 import BeautifulSoup as bs
from markdown2 import markdown as md
import html2text
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import urllib.parse
from fastapi.middleware.cors import CORSMiddleware

h2t = html2text.HTML2Text()
h2t.ignore_images = True
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ou defina domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
def index():
  return "Novelbin API!"

@app.get("/search/{query}")
def search(query):
    resp = requests.get(f"https://novelbin.com/ajax/search-novel?keyword={urllib.parse.quote_plus(query)}", headers={"User-Agent": "curl/4.0.0"}).text
    soup = bs(resp, 'lxml')
    lista = soup.select("a")[:-1]
    return {"sucesso": True, "resultado": [ {"nome": i.text.strip(), "url": i.get("href").split("/")[-1], "cover": f"https://novelbin.com/media/novel/{i.get('href').split('/')[-1]}.jpg"} for i in lista ]}

@app.get("/novel/{novel_id}")
def novel_info(novel_id):
  try:
    resp = requests.get(f"https://novelbin.com/b/{novel_id}#tab-chapters-title").text
    soup = bs(resp, 'lxml')
    title = soup.select_one("h3.title").text.strip()
    desc = soup.select_one("div.desc-text").text.strip()
    cover = f"https://novelbin.com/media/novel/{novel_id}.jpg"
    resp_chap = requests.get(f"https://novelbin.com/ajax/chapter-option?novelId={novel_id}").text
    soup_chap = bs(resp_chap, 'lxml')
    chapters = [ i.get("chapter-id") for i in soup_chap.select("option") ]
    return {"title": title, "desc": desc, "cover": cover, "chapters": chapters}
  except Exception as e:
    return {"Erro": str(e)}

@app.get("/novel/{novel_id}/{chapter_id}")
def chapter(novel_id, chapter_id):
    resp = requests.get(f"https://novelbin.com/b/{novel_id}/{chapter_id}").text
    soup = bs(resp, 'lxml')
    title = soup.select_one("a.novel-title").text.strip()
    subtitle = soup.select_one(".chr-text").text.strip()
    content = soup.select_one("#chr-content, #chapter-content")
    text = md("\n\n".join([ i.replace("\n", " ") for i in h2t.handle(str(content)).split("\n\n") ][:-2]))
    return {"title": title, "subtitle": subtitle, "content": text}
