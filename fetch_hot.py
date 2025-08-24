# -*- coding: utf-8 -*-
import json
import requests
from urllib.parse import urlparse, urlunparse

URL_API = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc&_signature=_02B4Z6wo00101tmIzpgAAIDA6h042Vf8tW7ZrMoAAN7WiUaRZW8zYaeBcCFCkYAKaOPTJHjwayMoJ4Xa3L5aQnIH1V9O0qiyg-EiGJGi5xCEflYNVJXQ74nwlsSfnLNtWxsO4NkM7WVNhrtO69"
URL_HOME = "https://www.toutiao.com/?is_new_connect=0&is_new_user=0&wid=1756018829399"

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"

def clean_url(url: str) -> str:
    """去掉 query/fragment，保留短链"""
    if not url:
        return url
    p = urlparse(url)
    return urlunparse((p.scheme or "https", p.netloc or "www.toutiao.com", p.path, "", "", ""))

def get_field(row, *keys, default=""):
    if not isinstance(row, dict):
        return default
    for k in keys:
        if k in row and row[k] is not None:
            return row[k]
    return default

def extract_fixed_top(j):
    raw = j.get("fixed_top_data") if isinstance(j, dict) else None
    # dict 直接取；dict.data；list[0] 都兜底
    cand = None
    if isinstance(raw, dict):
        cand = raw.get("data") if isinstance(raw.get("data"), dict) else raw
    elif isinstance(raw, list) and raw:
        cand = raw[0] if isinstance(raw[0], dict) else None
    if not cand and isinstance(j, dict):
        style = j.get("fixed_top_style")
        if isinstance(style, dict):
            cand = style
    if not cand:
        return None

    title = get_field(cand, "Title", "title", "FixedTopTitle")
    url   = get_field(cand, "Url", "url", "OpenUrl", "article_url")
    label = get_field(cand, "Label", "label", default="")
    if title and url:
        return {"rank": "置顶", "title": title.strip(), "url": clean_url(url), "label": label}
    return None

def main():
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "Referer": URL_HOME,
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    })
    r = sess.get(URL_API, timeout=15)
    r.raise_for_status()
    j = r.json()

    # 榜单数组（按顺序=1..50）
    arr = j.get("data") if isinstance(j, dict) else (j if isinstance(j, list) else [])
    arr = arr if isinstance(arr, list) else []

    items = []
    for i in range(1, 51):
        row = arr[i-1] if i-1 < len(arr) and isinstance(arr[i-1], dict) else {}
        title = get_field(row, "Title", "title")
        url   = get_field(row, "Url", "url")
        label = get_field(row, "Label", "label", default="")
        if title and url:
            items.append({
                "rank": i,
                "title": title.strip(),
                "url": clean_url(url),
                "label": label
            })
        else:
            items.append({
                "rank": i,
                "title": "",
                "url": "",
                "label": ""
            })

    top = extract_fixed_top(j)

    payload = {
        "source": "toutiao_hot_board",
        "generated_at": r.headers.get("Date", ""),  # 简单带个时间戳
        "top": top,
        "items": items
    }

    with open("hot.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("hot.json 已生成 ✅")

if __name__ == "__main__":
    main()
