import requests, re
from bs4 import BeautifulSoup
import tldextract, favicon
from fallback_utils import fallback_enrichment

EMAIL_REGEX = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
PHONE_REGEX = re.compile(r'\+?\d[\d\s\-\(\)]{7,}\d')

HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_soup(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        return BeautifulSoup(r.text, 'html.parser')
    except:
        return None

def extract_emails(text): return list(set(EMAIL_REGEX.findall(text)))
def extract_phones(text): return list(set(PHONE_REGEX.findall(text)))

def extract_social(soup):
    links = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        for word in ['linkedin.com', 'twitter.com', 'facebook.com']:
            if word in href:
                links.add(href)
    return list(links)

def extract_favicon(domain_url):
    try:
        icons = favicon.get(domain_url, timeout=3)
        return icons[0].url if icons else None
    except:
        return None

def scrape_domain(domain):
    domain = domain.lower().strip()
    if not domain.startswith('http'):
        domain = 'https://' + domain
    base = domain.rstrip('/')

    data = {
        "domain": base,
        "emails": [],
        "phones": [],
        "social_links": [],
        "title": "",
        "description": "",
        "favicon": extract_favicon(base),
        "revenue": None,
        "founders": None,
        "scraped_text": ""
    }
    pages = ["", "/about", "/contact"]
    text_accum = ""

    for p in pages:
        soup = get_soup(base + p)
        if not soup: continue

        if data["title"] == "":
            t = soup.find('title')
            data["title"] = t.text.strip() if t else ""

        if data["description"] == "":
            m = soup.find('meta', attrs={'name': 'description'})
            data["description"] = m['content'].strip() if m and m.get('content') else ""

        text = soup.get_text(separator=' ', strip=True)
        text_accum += text + " "

        data["emails"] += extract_emails(text)
        data["phones"] += extract_phones(text)
        data["social_links"] += extract_social(soup)

    # Deduplicate
    data["emails"] = list(set(data["emails"]))
    data["phones"] = list(set(data["phones"]))
    data["social_links"] = list(set(data["social_links"]))

    data["favicon"] = data["favicon"]
    data["scraped_text"] = text_accum[:2000]  # limit size
    data = fallback_enrichment(base, data)

    return data
