import os
import time
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from weasyprint import HTML

# === 설정 ===
CHROMEDRIVER_PATH = r"C:\tools\chromedriver-win64\chromedriver.exe"
SAVE_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "naver_cafe_posts")
os.makedirs(SAVE_DIR, exist_ok=True)

# === 디버깅 크롬 연결 ===
options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)

# === 시작 안내 ===
print('🧭 디버깅 모드 크롬에서 네이버 카페 로그인 후 작성자 검색까지 완료한 뒤 Enter를 누르세요.')
input("🔐 로그인 및 검색 완료되었으면 Enter...")

# === 현재 목록 페이지 주소 저장 ===
driver.switch_to.default_content()
list_url = driver.current_url  # 처음 목록 페이지 주소 저장

# === 파일 이름 필터 함수 ===
def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)[:100]

# === 게시글 수집 및 저장 함수 ===
def collect_and_save():
    driver.switch_to.default_content()
    driver.switch_to.frame("cafe_main")
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    posts = soup.select("a.article")
    links = ["https://cafe.naver.com" + p["href"] for p in posts if p.get("href")]
    print(f"📄 감지된 글 수: {len(links)}")

    for idx, link in enumerate(links, 1):
        try:
            driver.get(link)
            time.sleep(2)
            driver.switch_to.frame("cafe_main")

            soup = BeautifulSoup(driver.page_source, "html.parser")
            title_tag = soup.select_one("h3.title_text")
            content_tag = soup.select_one("div.se-main-container") or soup.select_one("div.ContentRenderer")

            if not title_tag or not content_tag:
                print(f"[⚠️] 본문 없음: {link}")
                continue

            title = title_tag.get_text(strip=True)
            html_content = f"<html><head><meta charset='utf-8'></head><body>{str(content_tag)}</body></html>"

            filename = sanitize_filename(title) + ".pdf"
            filepath = os.path.join(SAVE_DIR, filename)

            HTML(string=html_content).write_pdf(filepath)
            print(f"[{idx}] 저장 완료: {filename}")

            driver.switch_to.default_content()
        except Exception as e:
            print(f"[❌] 저장 실패 ({link}) - {e}")
            continue

    # 페이지 끝나면 목록 페이지로 복귀
    print("↩️ 목록 페이지로 돌아갑니다...")
    driver.get(list_url)
    time.sleep(2)

# === 수동 페이지 진행 루프 ===
while True:
    answer = input("\n현재 페이지를 처리하려면 Y, 종료하려면 N을 눌러주세요: ").strip().lower()
    if answer == 'y':
        collect_and_save()
    elif answer == 'n':
        print("🚪 종료합니다.")
        break
    else:
        print("❗ Y 또는 N만 입력 가능합니다.")

driver.quit()
print("✅ 모든 작업 완료!")
