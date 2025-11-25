import re
import time
import json
import requests
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from utils.file_parsers import parse_file_bytes
from utils.gemini_client import ask_gemini
from config import (PLAYWRIGHT_NAV_TIMEOUT, SOLVE_TOTAL_TIMEOUT,REQUEST_TIMEOUT, SYSTEM_PROMPT, USER_PROMPT)

def extract_submit_url(html: str):
    m = re.search(r"https?://[^\s'\"<>]+/submit[^\s'\"<>]*", html)
    return m.group(0) if m else None

def find_download_links(page):
    anchors = page.query_selector_all("a")
    urls = []
    for a in anchors:
        try:
            href = a.get_attribute("href")
            if not href:
                continue
            if any(href.lower().endswith(e) for e in [".csv", ".xlsx", ".xls", ".pdf"]):
                if href.startswith("http"):
                    urls.append(href)
                else:
                    base = page.url.rstrip("/")
                    urls.append(base + "/" + href.lstrip("/"))
        except Exception:
            continue
    return urls

def download_url_bytes(url: str, timeout=REQUEST_TIMEOUT):
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.content, url.split("/")[-1]

def build_prompt(question_text: str, parsed_files: dict):
    extracted = {"files": parsed_files}
    prompt = f"""System: {SYSTEM_PROMPT}

User: {USER_PROMPT}

Task:
{question_text}

ParsedData:
{json.dumps(extracted, indent=2)}

Return ONLY a JSON object containing the key "answer" with the value.
Example:
{{"answer": 12345}}
"""
    return prompt

def solve_quiz_url(url: str, total_timeout: int = SOLVE_TOTAL_TIMEOUT):
    start = time.time()
    result = {"solved": False, "answer": None, "submit_url": None, "submit_response": None, "log": []}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context()
        page = context.new_page()
        try:
            page.goto(url, timeout=PLAYWRIGHT_NAV_TIMEOUT * 1000)
            page.wait_for_load_state("networkidle", timeout=PLAYWRIGHT_NAV_TIMEOUT * 1000)
        except PWTimeout:
            result["log"].append("playwright navigation timeout")
        except Exception as e:
            result["log"].append(f"playwright goto error: {e}")

        html = page.content()
        # be careful: large text can be trimmed
        try:
            text = page.inner_text("body")[:20000]
        except Exception:
            text = re.sub(r"\s+", " ", html)[:20000]

        submit_url = extract_submit_url(html)
        result["submit_url"] = submit_url

        parsed_files = {}
        try:
            links = find_download_links(page)
            for link in links:
                if time.time() - start > total_timeout: break
                try:
                    bts, hint = download_url_bytes(link)
                    parsed_files[link] = parse_file_bytes(bts, hint)
                except Exception as e:
                    parsed_files[link] = {"error": str(e)}
        except Exception as e:
            result["log"].append(f"link discovery error: {e}")

        prompt = build_prompt(text, parsed_files)
        try:
            llm_output = ask_gemini(prompt)
        except Exception as e:
            result["log"].append(f"gemini error: {e}")
            llm_output = ""

        ans = None
        try:
            j = re.search(r"(\{[\s\S]*\})", llm_output)
            if j:
                parsed = json.loads(j.group(1))
                ans = parsed.get("answer")
            else:
                nums = re.findall(r"-?\d+\.?\d*", llm_output)
                if nums:
                    candidate = nums[0]
                    if "." in candidate:
                        ans = float(candidate)
                    else:
                        ans = int(candidate)
                else:
                    ans = llm_output.strip()
        except Exception:
            ans = llm_output.strip()

        result["answer"] = ans

        if not submit_url:
            try:
                form = page.query_selector("form")
                if form:
                    action = form.get_attribute("action")
                    if action:
                        if action.startswith("http"):
                            submit_url = action
                        else:
                            submit_url = page.url.rstrip("/") + "/" + action.lstrip("/")
                        result["submit_url"] = submit_url
            except Exception:
                pass

        if submit_url:
            payload = {"email": None, "secret": None, "url": url, "answer": ans}
            try:
                r = requests.post(submit_url, json=payload, timeout=REQUEST_TIMEOUT)
                try:
                    result["submit_response"] = r.json()
                except Exception:
                    result["submit_response"] = {"status_code": r.status_code, "text": r.text}
            except Exception as e:
                result["submit_response"] = {"error": str(e)}

        browser.close()

    result["solved"] = True
    result["duration_sec"] = time.time() - start
    return result

