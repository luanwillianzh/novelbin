import requests
from bs4 import BeautifulSoup as bs
from lxml import html
from markdown2 import markdown as md
import html2text
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import urllib.parse
from googletrans import Translator

h2t = html2text.HTML2Text()
h2t.ignore_images = True
t = Translator()
app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def index():
  return "Novelbin API!"

@app.get("/search/{query}")
def search(query):
  r = requests.get(f"https://novelbin.me/ajax/search-novel?keyword={query}").text
  h = html.fromstring(r)
  lista = [ (a.items()[0][1].split("/")[-1], a.text) for a in h.xpath("//a") ]
  return str(lista)

@app.get("/novel/{novel_id}")
def novel_info(novel_id):
  r = requests.get(f"http://104.18.37.248/novel-book/{novel_id}", headers={"Host": "novelbin.com"})
  if r.status_code == 404:
    return {"sucesso": False}
  else:
    h = bs(r.text, features="lxml")
    title = t.translate(html.fromstring(r.text).xpath("//h3[@class='title']/text()")[0]).text #.text.find_all("h3", {"class": "title"})[0].text, dest="pt").text
    desc = t.translate(h.find_all("div", {"class": "desc-text"})[0].text, dest="pt").text
    lista = [ a.values()[0] for a in html.fromstring(requests.get(f"https://novelbin.com/ajax/chapter-option?novelId={novel_id}").text).xpath("//option") ]
    return {"sucesso": True, "resultado": {"title": title, "desc": desc, "cover": f"https://novelbin.me/media/novel/{novel_id}.jpg", "chapters": lista}}

@app.get("/novel/{novel_id}/{chapter_id}")
def chapter(novel_id, chapter_id):
  r = requests.get(f"http://104.18.37.248/novel-book/{novel_id}", headers={"Host": "novelbin.com"})
  if r.status_code == 404:
    return {"sucesso": False}
  else:
    caps = {}
    lista = [ caps.update({a.values()[0]:f"http://104.18.37.248/b/{novel_id}/{a.values()[0]}"}) for a in html.fromstring(requests.get(f"https://novelbin.com/ajax/chapter-option?novelId={novel_id}").text).xpath("//option") ]
    if chapter_id in caps:
      r = requests.get(caps[chapter_id], headers={"Host": "novelbin.com"}).text
      h = bs(r, features="lxml")
      div = [ i.replace("\n", " ") for i in h2t.handle(str(h.find_all("div", {"class": "chr-c"})[0])).split("\n\n") ]
      title = "".join(h.find_all("span", {"class": "chr-text"})[0].text.replace("\n", "").split("  "))
      #
      #
      #
      #js = requests.get(f"https://translate.googleapis.com/translate_a/single?dt=t&dt=bd&dt=qc&dt=rm&dt=ex&client=gtx&hl=en&sl=auto&tl=pt&q={text}&dj=1&tk=536966.536966").json()
      #trad = "".join([ i["trans"] for i in js["sentences"] ])
      #epcontent = md(trad)
      #chapter = f'''<html><head><title>{title}</title></head><body><h1>{title}</h1>{div}</body></html>'''
      chapter = {"sucesso": True, "resultado": {"title": title, "content": div}}
      return chapter
    else:
      return {"sucesso": False}
