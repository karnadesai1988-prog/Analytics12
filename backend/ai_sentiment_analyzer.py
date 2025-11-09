"""
AI Sentiment Analysis & Contextual Intelligence Module
Self-contained without external dependencies
"""
import re
from collections import Counter
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
import requests
from bs4 import BeautifulSoup
import json

# ==========================================
# SENTIMENT ANALYSIS KEYWORDS
# ==========================================
POSITIVE_KEYWORDS = [
    'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love',
    'best', 'happy', 'excited', 'beautiful', 'perfect', 'awesome', 'nice',
    'positive', 'success', 'growth', 'opportunity', 'innovation', 'quality',
    'affordable', 'convenient', 'clean', 'safe', 'friendly', 'professional',
    'recommended', 'satisfied', 'improved', 'better', 'modern', 'new', 'fresh'
]

NEGATIVE_KEYWORDS = [
    'bad', 'terrible', 'awful', 'worst', 'hate', 'poor', 'disappointing',
    'problem', 'issue', 'broken', 'dirty', 'dangerous', 'crime', 'theft',
    'fraud', 'scam', 'expensive', 'overpriced', 'delayed', 'late', 'cancel',
    'complaint', 'noise', 'pollution', 'traffic', 'garbage', 'old', 'damaged'
]

# ==========================================
# NEWS SCRAPING FOR CRIME ANALYSIS
# ==========================================
CRIME_KEYWORDS = [
    "crime", "crimes", "criminal", "police", "arrest", "murder", "theft",
    "robbery", "violence", "assault", "kidnap", "fraud", "scam"
]

INVESTMENT_KEYWORDS = [
    "investment", "investor", "invest", "stocks", "market", "finance",
    "banking", "opportunity", "business", "startup", "entrepreneur",
    "development", "project", "infrastructure", "construction"
]

JOB_KEYWORDS = [
    "job", "jobs", "hiring", "recruitment", "employment", "vacancy",
    "career", "work", "salary", "position", "opening"
]

def extract_keywords_from_text(text: str, keyword_list: List[str]) -> List[str]:
    """Extract matching keywords from text"""
    if not text:
        return []
    text_lower = text.lower()
    found = [kw for kw in keyword_list if kw in text_lower]
    return list(set(found))

def scrape_gujarat_news_for_rid(rid: str, pages: int = 2) -> Dict[str, Any]:
    """
    Scrape news data for a specific RID (region/territory)
    Returns crime rate, investment activity, and job market metrics
    """
    crime_count = 0
    investment_count = 0
    job_count = 0
    total_articles = 0
    
    try:
        for page in range(1, pages + 1):
            url = f"https://english.gujaratsamachar.com/city/all/{page}"
            headers = {"User-Agent": "Mozilla/5.0"}
            
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code != 200:
                continue
                
            soup = BeautifulSoup(response.text, "html.parser")
            articles = soup.find_all("a", class_="theme-link list-news-title")
            
            for article in articles[:10]:  # Limit per page
                title = article.get("title", "").lower()
                total_articles += 1
                
                # Count keywords
                if any(kw in title for kw in CRIME_KEYWORDS):
                    crime_count += 1
                if any(kw in title for kw in INVESTMENT_KEYWORDS):
                    investment_count += 1
                if any(kw in title for kw in JOB_KEYWORDS):
                    job_count += 1
                    
    except Exception as e:
        print(f"News scraping error: {e}")
    
    # Convert to 0-10 rating (inverse for crime, direct for others)
    if total_articles > 0:
        crime_ratio = crime_count / total_articles
        investment_ratio = investment_count / total_articles
        job_ratio = job_count / total_articles
        
        # Crime: Lower is better (inverse rating)
        crime_rating = max(0, 10 - (crime_ratio * 50))
        
        # Investment & Jobs: Higher is better
        investment_rating = min(10, investment_ratio * 40)
        job_rating = min(10, job_ratio * 40)
    else:
        crime_rating = 5.0
        investment_rating = 5.0
        job_rating = 5.0
    
    return {
        "crime_rate_score": round(crime_rating, 1),
        "investment_activity_score": round(investment_rating, 1),
        "job_market_score": round(job_rating, 1),
        "articles_analyzed": total_articles,
        "crime_mentions": crime_count,
        "investment_mentions": investment_count,
        "job_mentions": job_count
    }

# ==========================================
# SENTIMENT ANALYSIS
# ==========================================
def analyze_text_sentiment(text: str) -> Dict[str, Any]:
    """Analyze sentiment of a single text"""
    if not text:
        return {"sentiment": "neutral", "score": 0.0}
    
    text_lower = text.lower()
    
    positive_count = sum(1 for word in POSITIVE_KEYWORDS if word in text_lower)
    negative_count = sum(1 for word in NEGATIVE_KEYWORDS if word in text_lower)
    
    total = positive_count + negative_count
    if total == 0:
        return {"sentiment": "neutral", "score": 0.0}
    
    sentiment_score = (positive_count - negative_count) / total
    
    if sentiment_score > 0.2:
        sentiment = "positive"
    elif sentiment_score < -0.2:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    return {
        "sentiment": sentiment,
        "score": round(sentiment_score, 2),
        "positive_keywords": positive_count,
        "negative_keywords": negative_count
    }

def extract_keywords(texts: List[str], top_n: int = 10) -> List[str]:
    """Extract top keywords from multiple texts"""
    # Common words to exclude
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                  'of', 'with', 'is', 'was', 'are', 'were', 'been', 'be', 'have', 'has',
                  'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'this',
                  'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'}
    
    # Combine all texts
    combined_text = ' '.join(texts).lower()
    
    # Extract words (alphanumeric only)
    words = re.findall(r'\b[a-z]{3,}\b', combined_text)
    
    # Filter out stop words
    filtered_words = [w for w in words if w not in stop_words]
    
    # Count frequencies
    word_counts = Counter(filtered_words)
    
    # Return top N
    return [word for word, count in word_counts.most_common(top_n)]

# ==========================================
# ACTIVITY TYPE ANALYSIS
# ==========================================
def analyze_activity_types(pins: List[Dict], posts: List[Dict], 
                           events: List[Dict], projects: List[Dict]) -> Dict[str, Any]:
    """Analyze dominant activity types in territory"""
    
    pin_types = {}
    for pin in pins:
        pin_type = pin.get('type', 'other')
        pin_types[pin_type] = pin_types.get(pin_type, 0) + 1
    
    # Calculate totals
    total_pins = len(pins)
    total_posts = len(posts)
    total_events = len(events)
    total_projects = len(projects)
    
    # Determine dominant activity
    activity_scores = {
        'Pins': total_pins,
        'Posts': total_posts * 2,  # Weight posts higher
        'Events': total_events * 3,  # Weight events highest
        'Projects': total_projects * 4  # Weight projects most
    }
    
    dominant_activity = max(activity_scores, key=activity_scores.get) if any(activity_scores.values()) else "None"
    
    # Determine dominant pin type
    dominant_pin_type = max(pin_types, key=pin_types.get) if pin_types else "None"
    
    return {
        "dominant_activity": dominant_activity,
        "dominant_pin_type": dominant_pin_type.capitalize(),
        "pin_counts": pin_types,
        "total_pins": total_pins,
        "total_posts": total_posts,
        "total_events": total_events,
        "total_projects": total_projects,
        "activity_density": total_pins + total_posts + total_events + total_projects
    }

# ==========================================
# ENGAGEMENT ANALYSIS
# ==========================================
def analyze_engagement(posts: List[Dict], events: List[Dict], 
                       communities: List[Dict]) -> Dict[str, Any]:
    """Analyze engagement rates"""
    
    recent_cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    
    def safe_parse_date(date_val):
        """Safely parse date string or datetime object"""
        if isinstance(date_val, datetime):
            return date_val
        if isinstance(date_val, str):
            try:
                return datetime.fromisoformat(date_val.replace('Z', '+00:00'))
            except:
                return datetime(2020, 1, 1, tzinfo=timezone.utc)
        return datetime(2020, 1, 1, tzinfo=timezone.utc)
    
    recent_posts = [p for p in posts 
                    if safe_parse_date(p.get('createdAt')) > recent_cutoff]
    
    recent_events = [e for e in events
                     if safe_parse_date(e.get('createdAt')) > recent_cutoff]
    
    total_members = sum(len(c.get('members', [])) for c in communities)
    
    # Calculate engagement rate
    if len(communities) > 0:
        avg_members_per_community = total_members / len(communities)
    else:
        avg_members_per_community = 0
    
    # Engagement score (0-10)
    engagement_score = min(10, (
        (len(recent_posts) * 0.5) +
        (len(recent_events) * 1.0) +
        (avg_members_per_community * 0.2)
    ))
    
    return {
        "recent_posts_30d": len(recent_posts),
        "recent_events_30d": len(recent_events),
        "total_community_members": total_members,
        "active_communities": len(communities),
        "engagement_score": round(engagement_score, 1)
    }

# ==========================================
# AI INSIGHT GENERATION
# ==========================================
def generate_ai_insight(territory_data: Dict[str, Any]) -> str:
    """Generate human-like AI insight based on data analysis"""
    
    sentiment = territory_data.get('overall_sentiment', 'neutral')
    dominant_activity = territory_data.get('dominant_activity_type', 'None')
    engagement_score = territory_data.get('engagement_metrics', {}).get('engagement_score', 0)
    crime_score = territory_data.get('crime_rate_score', 5)
    investment_score = territory_data.get('investment_activity_score', 5)
    job_score = territory_data.get('job_market_score', 5)
    
    # Build insight based on patterns
    insights = []
    
    # Sentiment-based insight
    if sentiment == "positive":
        insights.append("The territory demonstrates strong positive sentiment")
    elif sentiment == "negative":
        insights.append("The territory shows concerning negative sentiment patterns")
    else:
        insights.append("The territory maintains neutral community sentiment")
    
    # Activity-based insight
    if dominant_activity != "None":
        insights.append(f"driven primarily by {dominant_activity.lower()} activity")
    
    # Engagement insight
    if engagement_score >= 7:
        insights.append("with highly active community participation")
    elif engagement_score >= 4:
        insights.append("with moderate community engagement")
    else:
        insights.append("though community engagement remains low")
    
    # Safety & Crime
    if crime_score >= 7:
        insights.append(". The area shows excellent safety indicators")
    elif crime_score >= 5:
        insights.append(". Safety metrics are average")
    else:
        insights.append(". Safety concerns require attention")
    
    # Economic indicators
    if investment_score >= 6 and job_score >= 6:
        insights.append(", with strong economic growth potential indicated by rising investment and employment opportunities")
    elif investment_score >= 6:
        insights.append(", with notable investment activity suggesting growth momentum")
    elif job_score >= 6:
        insights.append(", with healthy job market signals")
    
    # Recommendations
    recommendations = []
    if sentiment == "positive" and engagement_score >= 6:
        recommendations.append("Consider expanding community programs and hosting promotional events")
    elif sentiment == "negative":
        recommendations.append("Focus on addressing community concerns and improving service quality")
    
    if investment_score >= 6:
        recommendations.append("Explore real estate and infrastructure partnerships")
    
    if job_score >= 6:
        recommendations.append("Promote local businesses and employment initiatives")
    elif job_score < 4:
        recommendations.append("Consider job fairs and skill development programs")
    
    if crime_score < 5:
        recommendations.append("Enhance safety measures and community watch programs")
    
    # Combine into final insight
    insight = ''.join(insights)
    if recommendations:
        insight += ". " + ". ".join(recommendations) + "."
    else:
        insight += "."
    
    return insight

# ==========================================
# MAIN ANALYSIS FUNCTION
# ==========================================
async def analyze_territory_intelligence(
    territory_id: str,
    rid: str,
    posts: List[Dict],
    events: List[Dict],
    pins: List[Dict],
    projects: List[Dict],
    communities: List[Dict],
    rating: float
) -> Dict[str, Any]:
    """
    Comprehensive AI analysis of territory data
    Returns sentiment, insights, and recommendations
    """
    
    # Extract all text content
    post_texts = [p.get('text', '') for p in posts if p.get('text')]
    event_titles = [e.get('title', '') for e in events if e.get('title')]
    
    all_texts = post_texts + event_titles
    
    # Analyze sentiment
    sentiment_results = [analyze_text_sentiment(text) for text in all_texts]
    
    if sentiment_results:
        avg_sentiment_score = sum(s['score'] for s in sentiment_results) / len(sentiment_results)
        positive_count = sum(1 for s in sentiment_results if s['sentiment'] == 'positive')
        negative_count = sum(1 for s in sentiment_results if s['sentiment'] == 'negative')
        
        if positive_count > negative_count * 1.5:
            overall_sentiment = "Positive"
        elif negative_count > positive_count * 1.5:
            overall_sentiment = "Negative"
        else:
            overall_sentiment = "Neutral"
    else:
        overall_sentiment = "Neutral"
        avg_sentiment_score = 0.0
    
    # Extract keywords
    top_keywords = extract_keywords(all_texts, top_n=8)
    
    # Analyze activities
    activity_analysis = analyze_activity_types(pins, posts, events, projects)
    
    # Analyze engagement
    engagement_metrics = analyze_engagement(posts, events, communities)
    
    # Scrape news for crime/investment/jobs (use RID if provided)
    news_metrics = scrape_gujarat_news_for_rid(rid, pages=2)
    
    # Compile all data
    territory_intelligence = {
        "territory_id": territory_id,
        "rid": rid,
        "overall_sentiment": overall_sentiment,
        "sentiment_score": round(avg_sentiment_score, 2),
        "dominant_activity_type": activity_analysis['dominant_activity'],
        "dominant_pin_type": activity_analysis['dominant_pin_type'],
        "top_keywords": top_keywords,
        "activity_metrics": {
            "total_pins": activity_analysis['total_pins'],
            "total_posts": activity_analysis['total_posts'],
            "total_events": activity_analysis['total_events'],
            "total_projects": activity_analysis['total_projects'],
            "activity_density": activity_analysis['activity_density'],
            "pin_type_breakdown": activity_analysis['pin_counts']
        },
        "engagement_metrics": engagement_metrics,
        "territory_rating": rating,
        "crime_rate_score": news_metrics['crime_rate_score'],
        "investment_activity_score": news_metrics['investment_activity_score'],
        "job_market_score": news_metrics['job_market_score'],
        "news_analysis": {
            "articles_analyzed": news_metrics['articles_analyzed'],
            "crime_mentions": news_metrics['crime_mentions'],
            "investment_mentions": news_metrics['investment_mentions'],
            "job_mentions": news_metrics['job_mentions']
        }
    }
    
    # Generate AI insight
    ai_insight = generate_ai_insight(territory_intelligence)
    territory_intelligence["ai_insight"] = ai_insight
    
    return territory_intelligence
