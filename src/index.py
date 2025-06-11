from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import requests
from bs4 import BeautifulSoup
import urllib.parse
app = FastAPI()

@app.get("/lancamentos")
def lancamentos():
    response = requests.get("https://illusia.com.br/lancamentos/").text
    soup = BeautifulSoup(response, 'html.parser')
    return {"sucesso": True, "resultado": [ {"url": novel.find_all("a")[0].get("href").split("/")[-2], "nome": novel.find_all("a")[0].get("title"), "cover": novel.find_all("img")[0].get("src")} for novel in soup.find_all("li", {"class": "_latest-updates"}) ]}

@app.get("/novel/{novel}")
def get_novel_info(novel):
    response = requests.get(f"https://illusia.com.br/story/{novel}/", verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')
    name = soup.select_one(".story__identity-title").text.strip().replace("\n", " ")
    desc = "\n".join([ p.text for p in soup.find_all("section", {"class": "story__summary content-section"})[0] ])
    cover = soup.select_one(".webfeedsFeaturedVisual")["src"]
    chapters = [(a.text, a["href"].split("/")[-2]) for a in soup.select(".chapter-group__list a")]
    genres = [ [a["href"].split("/")[-2], a.text] for a in soup.select("._taxonomy-genre") ]
    return {"nome": name, "desc": desc, "cover": cover, "chapters": chapters, "genres": genres}

@app.get("/novel/{novel}/chapter/{chapter}")
def get_chapter(novel, chapter):
    response = requests.get(f"https://illusia.com.br/story/{novel}/{chapter}/", verify=False)
    soup = BeautifulSoup(response.text)
    title = soup.select_one(".chapter__story-link").text.strip().replace("\n", " ")
    try:
      subtitle = soup.select_one(".chapter__title").text.strip().replace("\n", " ")
    except:
      subtitle = ""
    content = str(soup.select_one("#chapter-content"))
    return {"title": title, "subtitle": subtitle, "content": content}

@app.get("/search/{text}")
def search(text):
    url = f"https://illusia.com.br/?s={urllib.parse.quote_plus(text)}&post_type=fcn_story&sentence=0&orderby=modified&order=desc&age_rating=Any&story_status=Any&miw=0&maw=0&genres=&fandoms=&characters=&tags=&warnings=&authors=&ex_genres=&ex_fandoms=&ex_characters=&ex_tags=&ex_warnings=&ex_authors="
    resp = requests.post(url, verify=False).text
    soup = BeautifulSoup(resp, 'html.parser')
    return {"sucesso": True, "resultado": [ {"nome": a.find_all("a")[0].text, "url": a.find_all("a")[0].get("href").split("/")[-2], "cover": a.find_all("img")[0].get("src")} for a in soup.find_all("li", {"class": "card"}) ]}
