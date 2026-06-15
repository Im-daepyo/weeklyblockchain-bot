"""
위클리블록체인 -> 텔레그램 자동 송출 봇

- 여러 카테고리 RSS를 읽어서 새 기사만 텔레그램 채널로 보냅니다.
- Coinness(속보) 작성자 글은 자동 제외합니다.
- 같은 기사가 여러 카테고리에 걸쳐 있어도 한 번만 보냅니다(중복 제거).
- 기사 제목을 누르면 바로 기사로 가는 링크(미리보기 이미지 포함)로 보냅니다.
- 본문/작성자/키워드 줄은 넣지 않아 깔끔합니다.
"""

import json
import os
import re
import time
from pathlib import Path

import feedparser
import requests

# ─────────────────────────────────────────────────────────────
# 설정 (여기만 바꾸면 됩니다)
# ─────────────────────────────────────────────────────────────

BASE = "https://www.weeklyblockchain.co.kr/rss/category/code/"

# 받고 싶은 카테고리 코드. 빼고 싶으면 그 줄을 지우거나 # 으로 주석 처리하세요.
CATEGORY_CODES = [
    "X6V7",            # 시세
    "business",        # MARKET
    "cryptocurrency",  # COINS / 메이저코인L1
    "U7VR",            # 트레이더
    "virtual-worlds",  # EARN / 머니메이킹
    "coinbase",        # 한국 거래소
    "binance",         # 글로벌 거래소
    "ai",              # AI
    "ai-news",         # AI News
    "legal-framework", # 규제 동향
    "VIQP",            # 글로벌뉴스
    "conference",      # 컨퍼런스
    "event",           # Event
]

# 제외할 작성자(소문자). 속보 소스인 Coinness 를 거릅니다.
EXCLUDED_AUTHORS = {"coinness"}

# 한 번 실행에서 최대 몇 개까지 보낼지(과도한 도배 방지). 나머지는 다음 실행 때 보냅니다.
MAX_POST_PER_RUN = 20

# 상태 파일 보관 개수 상한
MAX_SEEN = 3000

# ─────────────────────────────────────────────────────────────
# 내부 동작
# ─────────────────────────────────────────────────────────────

SEEN_FILE = Path("seen.json")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; WBNewsBot/1.0)"}

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


def load_seen():
    if SEEN_FILE.exists():
        try:
            data = json.loads(SEEN_FILE.read_text(encoding="utf-8"))
            return list(data.get("seen", [])), bool(data.get("initialized", False))
        except Exception:
            return [], False
    return [], False


def save_seen(seen, initialized):
    seen = seen[-MAX_SEEN:]
    SEEN_FILE.write_text(
        json.dumps({"initialized": initialized, "seen": seen}, ensure_ascii=False),
        encoding="utf-8",
    )


def fetch_feed(code):
    url = BASE + code
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        return feedparser.parse(r.content)
    except Exception as e:
        print(f"[warn] feed error {code}: {e}")
        return None


def article_id(entry):
    raw = entry.get("id") or entry.get("link") or ""
    m = re.search(r"/articles/(\d+)", raw) or re.search(r"idxno=(\d+)", raw)
    return m.group(1) if m else raw


def entry_author(entry):
    return (entry.get("author") or "").strip().lower()


def escape_html(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def collect_new(seen_set):
    found = {}  # id -> item (카테고리 간 중복 제거)
    for code in CATEGORY_CODES:
        feed = fetch_feed(code)
        if not feed:
            continue
        for entry in feed.entries:
            aid = article_id(entry)
            if not aid or aid in seen_set or aid in found:
                continue
            if entry_author(entry) in EXCLUDED_AUTHORS:
                continue
            link = entry.get("link", "")
            if not link:
                continue
            found[aid] = {
                "id": aid,
                "title": (entry.get("title") or "(제목 없음)").strip(),
                "link": link,
                "published": entry.get("published_parsed"),
            }
    # 발행 시각 오래된 순으로 정렬(채널에 시간 순서대로 올라가게)
    return sorted(found.values(), key=lambda it: it["published"] or time.gmtime(0))


def send(item):
    text = f'<b><a href="{item["link"]}">{escape_html(item["title"])}</a></b>'
    return requests.post(
        TELEGRAM_API,
        data={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,  # 미리보기(이미지+제목 클릭) 켜기
        },
        timeout=30,
    )


def main():
    seen, initialized = load_seen()
    seen_set = set(seen)
    new_items = collect_new(seen_set)

    # 첫 실행: 기존 기사는 전부 '본 것'으로 표시(도배 방지), 최신 1건만 테스트로 전송
    if not initialized:
        for it in new_items:
            seen.append(it["id"])
        if new_items:
            resp = send(new_items[-1])
            print(f"[init] test post status={resp.status_code}")
        save_seen(seen, True)
        print(f"[init] seeded {len(new_items)} articles (no flood).")
        return

    posted = 0
    for it in new_items:
        if posted >= MAX_POST_PER_RUN:
            print("[info] hit per-run cap; rest will post next run.")
            break
        resp = send(it)
        if resp.status_code == 200 and resp.json().get("ok"):
            seen.append(it["id"])
            posted += 1
            print(f"[ok] {it['id']} {it['title']}")
            time.sleep(1)  # 가벼운 속도 제한
        else:
            print(f"[fail] {it['id']}: {resp.status_code} {resp.text[:200]}")
            # 실패한 건 seen 에 안 넣어서 다음 실행 때 재시도

    save_seen(seen, True)
    print(f"[done] posted {posted} new article(s).")


if __name__ == "__main__":
    main()
