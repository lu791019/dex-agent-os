"""Web 內容擷取模組 — 三層 fallback 鏈

用法：
  from lib.web_extract import extract_url_content
  title, text = extract_url_content("https://example.com/article")

Fallback 鏈：
  1. trafilatura fetch + extract（主要）
  2. requests/urllib fetch + trafilatura extract（trafilatura fetcher 失敗時）
  3. requests/urllib fetch + BeautifulSoup 基本擷取（<article>/<main> 區塊）
  4. 回傳 None + 提示使用 firecrawl + --file 模式
"""

from __future__ import annotations

import sys


def _fetch_html(url: str) -> str | None:
    """用 requests 或 urllib 取得 HTML 原始碼。"""
    try:
        import requests
        resp = requests.get(url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
        resp.raise_for_status()
        return resp.text
    except ImportError:
        pass
    except Exception as e:
        print(f"[web_extract] requests fetch failed: {e}", file=sys.stderr)

    # fallback: urllib
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"[web_extract] urllib fetch failed: {e}", file=sys.stderr)

    return None


def _bs4_extract(html: str) -> tuple[str | None, str | None]:
    """用 BeautifulSoup 做基本擷取：找 <article>/<main> 區塊。"""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return None, None

    soup = BeautifulSoup(html, "html.parser")

    # 標題
    title = None
    title_tag = soup.find("title")
    if title_tag:
        title = title_tag.get_text(strip=True)

    # 內容：優先找 <article>，其次 <main>，最後 <body>
    content_tag = soup.find("article") or soup.find("main") or soup.find("body")
    if not content_tag:
        return title, None

    # 移除 script/style/nav/footer
    for tag in content_tag.find_all(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    text = content_tag.get_text(separator="\n", strip=True)
    # 過濾太短的結果
    if len(text) < 100:
        return title, None

    return title, text


def extract_url_content(url: str) -> tuple[str | None, str | None]:
    """擷取 URL 的文字內容，回傳 (title, text)。

    三層 fallback 鏈：
      1. trafilatura fetch + extract
      2. requests/urllib fetch + trafilatura extract
      3. requests/urllib fetch + BeautifulSoup
      4. 回傳 (None, None) + 提示

    Returns:
        (title, text) — 成功時回傳標題和內文；失敗時回傳 (None, None)
    """
    # Layer 1: trafilatura fetch + extract
    try:
        import trafilatura
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, include_comments=False, include_tables=True)
            if text and len(text) >= 100:
                metadata = trafilatura.extract(downloaded, output_format="xmltei", include_comments=False)
                title = None
                if metadata:
                    import xml.etree.ElementTree as ET
                    try:
                        root = ET.fromstring(metadata)
                        ns = {"tei": "http://www.tei-c.org/ns/1.0"}
                        title_elem = root.find(".//tei:title", ns)
                        if title_elem is not None and title_elem.text:
                            title = title_elem.text.strip()
                    except ET.ParseError:
                        pass
                print(f"[web_extract] Layer 1 OK: trafilatura ({len(text)} chars)", file=sys.stderr)
                return title, text
    except Exception as e:
        print(f"[web_extract] Layer 1 failed: {e}", file=sys.stderr)

    # Layer 2: manual fetch + trafilatura extract
    html = _fetch_html(url)
    if html:
        try:
            import trafilatura
            text = trafilatura.extract(html, include_comments=False, include_tables=True)
            if text and len(text) >= 100:
                title = None
                try:
                    metadata = trafilatura.extract(html, output_format="xmltei", include_comments=False)
                    if metadata:
                        import xml.etree.ElementTree as ET
                        root = ET.fromstring(metadata)
                        ns = {"tei": "http://www.tei-c.org/ns/1.0"}
                        title_elem = root.find(".//tei:title", ns)
                        if title_elem is not None and title_elem.text:
                            title = title_elem.text.strip()
                except Exception:
                    pass
                print(f"[web_extract] Layer 2 OK: fetch + trafilatura ({len(text)} chars)", file=sys.stderr)
                return title, text
        except Exception as e:
            print(f"[web_extract] Layer 2 trafilatura failed: {e}", file=sys.stderr)

        # Layer 3: fetch + BeautifulSoup
        title, text = _bs4_extract(html)
        if text:
            print(f"[web_extract] Layer 3 OK: fetch + BeautifulSoup ({len(text)} chars)", file=sys.stderr)
            return title, text

    # Layer 4: all failed
    print("[web_extract] 所有擷取方式均失敗", file=sys.stderr)
    print(f"  建議使用 firecrawl 抓取後以 --file 模式處理：", file=sys.stderr)
    print(f"  使用 /firecrawl skill 抓取 {url} 存為本地檔案", file=sys.stderr)
    print(f"  然後執行 ./bin/agent learning-note --file <path> --title \"...\"", file=sys.stderr)
    return None, None
