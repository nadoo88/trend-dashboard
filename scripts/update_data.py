#!/usr/bin/env python3
"""매일 08:00 KST에 GitHub Actions가 실행 → data.json 생성.
표준 라이브러리만 사용 (의존성 없음)."""
import json, re, urllib.request, urllib.parse, xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
NOW = datetime.now(KST)

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (TrendDashboard)"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()

def rss_items(url):
    try:
        root = ET.fromstring(fetch(url))
        out = []
        for it in root.iter("item"):
            def g(tag):
                el = it.find(tag)
                return (el.text or "").strip() if el is not None and el.text else ""
            out.append({"title": g("title"), "link": g("link"),
                        "source": g("source"), "pubDate": g("pubDate")})
        return out
    except Exception as e:
        print("RSS 실패:", url, e)
        return []

def news_rss(query, days=3):
    q = urllib.parse.quote(f"{query} when:{days}d")
    return rss_items(f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko")

CLEAN = re.compile(r"[()→【】\[\]/·…]")
def clean_q(t):
    return re.sub(r"\s+", " ", CLEAN.sub(" ", t)).strip()

QUOTED = re.compile(r"['\u2018\"\u201C\u300C]([^'\u2019\"\u201D\u300D]{2,24})['\u2019\"\u201D\u300D]")
def extract_q(title):
    m = QUOTED.search(title)
    if m:
        return m.group(1)
    return " ".join(clean_q(title).split(" ")[:5])

def parse_pub(s):
    try:
        return parsedate_to_datetime(s).astimezone(KST)
    except Exception:
        return NOW

# ── 1) 실시간 검색어 (구글 트렌드 KR) ──
trends = []
for it in rss_items("https://trends.google.co.kr/trending/rss?geo=KR")[:12]:
    if it["title"]:
        trends.append(it["title"])

# ── 2) 이슈 뉴스 ──
news = []
for it in news_rss("숏폼 챌린지 OR 밈 유행 OR 아이돌 컴백", days=2)[:8]:
    title = it["title"].split(" - ")[0].strip()
    if title:
        news.append({"title": title, "link": it["link"]})

# ── 3) HOT 랭킹 자동 수집 (클라이언트와 동일한 점수 로직) ──
HOT_FEEDS = [
    {"q": "숏폼 챌린지 유행",   "tag": "챌린지", "plats": ["tiktok", "reels"],  "w": 12},
    {"q": "밈 유행 화제",       "tag": "밈",     "plats": ["x", "threads"],     "w": 12},
    {"q": "아이돌 컴백 챌린지", "tag": "K-POP",  "plats": ["tiktok", "x"],      "w": 10},
    {"q": "틱톡 릴스 인기",     "tag": "숏폼",   "plats": ["tiktok", "reels"],  "w": 8},
    {"q": "AI 콘텐츠 화제",     "tag": "AI",     "plats": ["x", "reels"],       "w": 8},
]
collected = []
for f in HOT_FEEDS:
    for it in news_rss(f["q"], days=3)[:8]:
        title = it["title"].split(" - ")[0].strip()
        if len(title) < 8:
            continue
        pub = parse_pub(it["pubDate"])
        hours = max(0.0, (NOW - pub).total_seconds() / 3600)
        if hours > 72:
            continue
        score = f["w"] + max(0, 72 - hours) / 6
        if re.search(r"챌린지|밈|유행|화제|열풍|돌풍|인기", title):
            score += 8
        if re.search(r"컴백|신곡|데뷔", title):
            score += 4
        collected.append({
            "plats": f["plats"], "tag": f["tag"], "t": title,
            "q": extract_q(title),
            "heat": (it["source"] + " · " if it["source"] else "") + pub.strftime("%m/%d %H:%M"),
            "article": it["link"], "score": score,
            "d": "최근 3일 내 뉴스에서 화제로 잡힌 소재. 지금 탑승하면 최신성 가중치를 받는 구간.",
        })

collected.sort(key=lambda c: -c["score"])
seen, hot = set(), []
for c in collected:
    key = re.sub(r"\s", "", c["t"])[:14]
    if key in seen:
        continue
    seen.add(key)
    c.pop("score", None)
    hot.append(c)
    if len(hot) >= 10:
        break

data = {
    "updatedAtKST": NOW.strftime("%Y-%m-%d %H:%M"),
    "trends": trends, "news": news, "hot": hot,
}
with open("data.json", "w", encoding="utf-8") as fp:
    json.dump(data, fp, ensure_ascii=False, indent=1)

print(f"완료: 검색어 {len(trends)} / 뉴스 {len(news)} / HOT {len(hot)}")
