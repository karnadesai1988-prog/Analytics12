import requests
from bs4 import BeautifulSoup
import time
import json
from typing import Dict, List, Any

# Keyword Tags for Classification
KEYWORD_TAGS = [
    "crime", "crimes", "criminal", "police", "arrest", "murder", "theft", "robbery",
    "investment", "investor", "invest", "stocks", "market", "finance", "banking",
    "opportunity", "opportunities", "business", "startup", "entrepreneur",
    "education", "school", "university", "student", "exam",
    "health", "hospital", "medical", "doctor", "patient", "disease",
    "politics", "government", "election", "minister", "party",
    "technology", "tech", "digital", "software", "app", "AI",
    "sports", "cricket", "football", "player", "match", "tournament",
    "accident", "crash", "collision", "injured", "death",
    "festival", "celebration", "cultural", "religious",
    "infrastructure", "construction", "development", "project",
    "weather", "rain", "temperature", "climate", "flood",
    "property", "real estate", "housing", "apartment", "rent", "lease"
]

def extract_tags(text: str) -> List[str]:
    """Extract matching tags from title or content."""
    if not text:
        return []
    
    text_lower = text.lower()
    found_tags = []
    
    for tag in KEYWORD_TAGS:
        if tag.lower() in text_lower:
            found_tags.append(tag)
    
    return sorted(list(set(found_tags)))

def scrape_gujarat_samachar_page(page_num: int) -> List[Dict]:
    """Scrape headlines from a single Gujarat Samachar city page."""
    url = f"https://english.gujaratsamachar.com/city/all/{page_num}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error loading page {page_num}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    headlines = []

    for a_tag in soup.find_all("a", class_="theme-link list-news-title"):
        title = a_tag.get("title", "").strip()
        link = a_tag.get("href", "").strip()

        if not link.startswith("http"):
            link = "https://english.gujaratsamachar.com" + link

        if title:
            headlines.append({"title": title, "link": link})

    return headlines

def scrape_article_content(url: str) -> str:
    """Extract full article text from a news URL."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error fetching {url}: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    paragraphs = soup.find_all("p")
    content = []
    for p in paragraphs:
        text = p.get_text(strip=True)
        if text and "advertisement" not in " ".join(p.get("class", [])).lower():
            content.append(text)

    article_text = " ".join(content).strip()
    return article_text if article_text else None

def analyze_news_metrics(pages: int = 2) -> Dict[str, Any]:
    """Scrape and analyze news for territory metrics."""
    crime_count = 0
    investment_count = 0
    job_count = 0
    property_count = 0
    infrastructure_count = 0
    total_articles = 0
    
    all_articles = []
    
    try:
        for page in range(1, pages + 1):
            headlines = scrape_gujarat_samachar_page(page)
            
            for headline in headlines[:5]:  # Limit to 5 per page for speed
                total_articles += 1
                title = headline['title'].lower()
                
                # Extract tags
                tags = extract_tags(headline['title'])
                
                # Count keywords
                if any(kw in title for kw in ['crime', 'criminal', 'police', 'arrest', 'theft', 'robbery']):
                    crime_count += 1
                if any(kw in title for kw in ['investment', 'invest', 'business', 'startup', 'entrepreneur']):
                    investment_count += 1
                if any(kw in title for kw in ['job', 'employment', 'hiring', 'recruitment']):
                    job_count += 1
                if any(kw in title for kw in ['property', 'real estate', 'housing', 'apartment', 'rent']):
                    property_count += 1
                if any(kw in title for kw in ['infrastructure', 'construction', 'development', 'project']):
                    infrastructure_count += 1
                
                all_articles.append({
                    'title': headline['title'],
                    'tags': tags
                })
                
    except Exception as e:
        print(f"News scraping error: {e}")
    
    # Calculate scores (0-10 scale)
    if total_articles > 0:
        crime_ratio = crime_count / total_articles
        investment_ratio = investment_count / total_articles
        job_ratio = job_count / total_articles
        property_ratio = property_count / total_articles
        infrastructure_ratio = infrastructure_count / total_articles
        
        # Crime: Lower is better (inverse rating)
        crime_score = max(0, 10 - (crime_ratio * 40))
        
        # Others: Higher is better
        investment_score = min(10, investment_ratio * 50)
        job_score = min(10, job_ratio * 50)
        property_score = min(10, property_ratio * 50)
        infrastructure_score = min(10, infrastructure_ratio * 50)
    else:
        crime_score = 5.0
        investment_score = 5.0
        job_score = 5.0
        property_score = 5.0
        infrastructure_score = 5.0
    
    # Calculate livability index (weighted average)
    livability_index = (
        (crime_score * 0.3) +  # Safety is important
        (infrastructure_score * 0.25) +  # Infrastructure matters
        (property_score * 0.2) +  # Housing availability
        (job_score * 0.15) +  # Employment
        (investment_score * 0.1)  # Economic growth
    )
    
    return {
        'crime_rate_score': round(crime_score, 1),
        'investment_activity_score': round(investment_score, 1),
        'job_market_score': round(job_score, 1),
        'property_market_score': round(property_score, 1),
        'infrastructure_score': round(infrastructure_score, 1),
        'livability_index': round(livability_index, 1),
        'articles_analyzed': total_articles,
        'crime_mentions': crime_count,
        'investment_mentions': investment_count,
        'job_mentions': job_count,
        'property_mentions': property_count,
        'infrastructure_mentions': infrastructure_count,
        'articles': all_articles
    }
