import requests
import feedparser

def search_arxiv(query, max_results=10):
    base_url = "http://export.arxiv.org/api/query?"
    search_query = f"search_query=all:{query}&start=0&max_results={max_results}"
    url = base_url + search_query

    response = requests.get(url)
    feed = feedparser.parse(response.text)

    papers = []
    for entry in feed.entries:
        papers.append({
            "title": entry.title,
            "authors": [author.name for author in entry.authors],
            "summary": entry.summary,
            "published": entry.published,
            "link": entry.link
        })
    return papers

papers = search_arxiv("deep research agent", 100)
for p in papers:
    print(f"📄 {p['title']}\n   {p['link']}\n ")
