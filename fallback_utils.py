# fallback_utils.py

from googlesearch import search
import requests, re
from bs4 import BeautifulSoup

EMAIL_REGEX = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
PHONE_REGEX = re.compile(r'\+?\d[\d\-\s\(\)]{7,}\d')

HEADERS = {"User-Agent": "Mozilla/5.0"}

def find_first_page(query):
    try:
        return next(search(query, num_results=1))
    except StopIteration:
        return None

def extract_from_url(url, regex):
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        matches = regex.findall(r.text)
        return matches
    except:
        return []

def fallback_enrichment(domain, data):
    base = domain.replace('https://', '').replace('http://', '').split('/')[0]

    if not data.get("emails"):
        q = f"@{base} email"
        url = find_first_page(q)
        if url:
            emails = extract_from_url(url, EMAIL_REGEX)
            data["emails"] = list(set(emails))

    if not data.get("phones"):
        q = f"{base} phone number"
        url = find_first_page(q)
        if url:
            phones = extract_from_url(url, PHONE_REGEX)
            data["phones"] = list(set(phones))

    # Revenue fallback
    qrev = f"{base} revenue"
    urlrev = find_first_page(qrev)
    if urlrev:
        text = extract_from_url(urlrev, re.compile(r'\$[0-9.,]+ (million|billion)', re.IGNORECASE))
        data["revenue"] = text[0] if text else None

    # Founder search
    qf = f"{base} founder"
    urlf = find_first_page(qf)
    if urlf:
        try:
            page = requests.get(urlf, headers=HEADERS, timeout=5)
            soup = BeautifulSoup(page.text, 'html.parser')
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                if "founder" in p.text.lower() or "ceo" in p.text.lower():
                    data["founders"] = p.text.strip()
                    break
        except:
            pass

    return data
