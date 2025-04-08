import requests
from bs4 import BeautifulSoup as bs
from markdown2 import markdown as md
import html2text
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import urllib.parse

h2t = html2text.HTML2Text()
h2t.ignore_images = True
app = FastAPI()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://novelbin.com",
}

def is_invalid_html(html: str) -> bool:
    return (
        "Access denied" in html or
        "cloudflare" in html.lower() or
        "403 Forbidden" in html or
        "404 Not Found" in html or
        "Just a moment..." in html or
        "<title>Document</title>" in html or
        len(html.strip()) < 500
    )

@app.get("/", response_class=HTMLResponse)
def index():
    return "Novelbin API!"

@app.get("/search/{query}")
def search(query):
    try:
        resp = requests.get(
            f"https://novelbin.com/ajax/search-novel?keyword={urllib.parse.quote_plus(query)}",
            headers=HEADERS
        ).text

        if is_invalid_html(resp):
            return {"erro": "Conteúdo inválido recebido. Possível bloqueio ou erro na pesquisa."}

        soup = bs(resp, 'lxml')
        lista = soup.select("a")[:-1] if soup.select("a") else []

        return {
            "sucesso": True,
            "resultado": [
                {
                    "nome": i.text.strip(),
                    "url": i.get("href").split("/")[-1],
                    "cover": f"https://novelbin.com/media/novel/{i.get('href').split('/')[-1]}.jpg"
                } for i in lista
            ]
        }
    except Exception as e:
        return {"erro": str(e)}

@app.get("/novel/{novel_id}")
def novel_info(novel_id):
    try:
        resp = requests.get(
            f"https://novelbin.com/b/{novel_id}#tab-chapters-title",
            headers=HEADERS
        ).text

        if is_invalid_html(resp):
            return {"erro": "A página retornou um conteúdo inesperado. Possível bloqueio ou ID inválido."}

        soup = bs(resp, 'lxml')
        title_tag = soup.select_one("h3.title")
        desc_tag = soup.select_one("div.desc-text")

        if not title_tag or not desc_tag:
            return {"erro": "Não foi possível extrair o título ou descrição. Verifique o ID."}

        title = title_tag.text.strip()
        desc = desc_tag.text.strip()
        cover = f"https://novelbin.com/media/novel/{novel_id}.jpg"

        resp_chap = requests.get(
            f"https://novelbin.com/ajax/chapter-option?novelId={novel_id}",
            headers=HEADERS
        ).text

        if is_invalid_html(resp_chap):
            return {"erro": "A lista de capítulos não pôde ser carregada. Possível bloqueio ou erro no ID."}

        soup_chap = bs(resp_chap, 'lxml')
        chapters = [i.get("chapter-id") for i in soup_chap.select("option")]

        return {"title": title, "desc": desc, "cover": cover, "chapters": chapters}

    except Exception as e:
        return {"erro": str(e)}

@app.get("/novel/{novel_id}/{chapter_id}")
def chapter(novel_id, chapter_id):
    try:
        resp = requests.get(
            f"https://novelbin.com/b/{novel_id}/{chapter_id}",
            headers=HEADERS
        ).text

        if is_invalid_html(resp):
            return {"erro": "Capítulo não carregado corretamente. Possível bloqueio ou ID inválido."}

        soup = bs(resp, 'lxml')
        title_tag = soup.select_one("a.novel-title")
        subtitle_tag = soup.select_one(".chr-text")
        content = soup.select_one("#chr-content, #chapter-content")

        if not title_tag or not subtitle_tag or not content:
            return {"erro": "Conteúdo do capítulo incompleto ou não encontrado."}

        title = title_tag.text.strip()
        subtitle = subtitle_tag.text.strip()

        text = md("\n\n".join([
            i.replace("\n", " ") for i in h2t.handle(str(content)).split("\n\n")
        ]))

        return {"title": title, "subtitle": subtitle, "content": text}

    except Exception as e:
        return {"erro": str(e)}
