import requests
from bs4 import BeautifulSoup as bs
from lxml import html
from markdown2 import markdown as md
from html2text import html2text as h2t
from googletrans import Translator as trans
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

t = trans()
app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def index():
  return "Hello World!"

@app.get("/search/{query}")
def search(query):
  r = requests.get(f"https://novelbin.me/ajax/search-novel?keyword={query}").text
  h = html.fromstring(r)
  lista = [ (a.items()[0][1].split("/")[-1], a.text) for a in h.xpath("//a") ]
  return str(lista)

@app.get("/novel/{novel_id}")
def novel_info(novel_id):
  r = requests.get(f"https://novelbin.me/novel-book/{novel_id}")
  if r.status_code == 404:
    return {"sucesso": False}
  else:
    h = bs(r.text, features="lxml")
    title = t.translate(html.fromstring(r.text).xpath("//h3[@class='title']/text()")[0]) #.text.find_all("h3", {"class": "title"})[0].text, dest="pt").text
    desc = t.translate(h.find_all("div", {"class": "desc-text"})[0].text, dest="pt").text
    caps = {}
    lista = [ caps.update({a.values()[0]:a.values()[1]}) for a in html.fromstring(requests.get(f"https://novelbin.com/ajax/chapter-option?novelId={novel_id}").text).xpath("//option") ]
    return {"sucesso": True, "resultado": {"title": title, "desc": desc, "cover": f"https://novelbin.me/media/novel/{novel_id}.jpg", "chapters": caps}}

@app.get("/novel/{novel_id}/{chapter_id}")
def chapter(novel_id, chapter_id):
  r = requests.get(f"https://novelbin.me/novel-book/{novel_id}")
  if r.status_code == 404:
    return {"sucesso": False}
  else:
    caps = {}
    lista = [ caps.update({a.values()[0]:a.values()[1]}) for a in html.fromstring(requests.get(f"https://novelbin.com/ajax/chapter-option?novelId={novel_id}").text).xpath("//option") ]
    if chapter_id in caps:
      r = requests.get(caps[chapter_id]).text
      h = bs(r, features="lxml")
      div = str(h.find_all("div", {"class": "chr-c"})[0])
      title = str(h.find_all("span", {"class": "chr-text"})[0])
      title = html.fromstring(title).xpath("//text()")[0]
      text = h2t(div).split("\n\n")
      js = trans().translate(text, dest="pt")
      trad = "\n\n".join([ i.text for i in js])
      epcontent = md(trad)
      chapter = f'''<html><head><title>{title}</title></head><body><h1>{title}</h1>{epcontent}</body></html>'''
      return HTMLResponse(chapter, status_code=200)
    else:
      return {"sucesso": False}
