import ssl
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from slack_sdk import WebClient
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
import time
import warnings
from urllib3.exceptions import InsecureRequestWarning
from googletrans import Translator

ssl._create_default_https_context = ssl._create_unverified_context
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

class NewsScraper:
    def __init__(self):
        self.options = Options()
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.48"
        self.options.add_experimental_option("prefs", {"safebrowsing.enabled": True})
        self.options.add_experimental_option("detach", True)
        self.options.add_argument("--start-maximized")
        self.options.add_argument('user-agent=' + user_agent)
        self.driver = webdriver.Chrome('chromedriver', options=self.options)
        max_wait_time = 60
        self.wait = WebDriverWait(self.driver, max_wait_time)
        self.translator = Translator()

    def parse_date(self, date):
        try:
            return datetime.strptime(date, "%B %d, %Y")
        except ValueError:
            print(f"날짜 형식이 일치하지 않습니다: {date}")
            return datetime.now()

    def translate_text(self, text, target_lang='ko'):
        translation = self.translator.translate(text, dest=target_lang)
        return translation.text

    def scrape_news_articles(self):
        url = "https://securityaffairs.com/must-read"
        self.driver.get(url)

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        articles = []
        news_blocks = soup.find_all('div', class_='news-card')

        for news_block in news_blocks:
            image_url = news_block.find('div', class_='news-card-pic').find('img')['src']
            date = news_block.find('p', class_='cat-date').contents[-1].strip()
            article_title = news_block.find('h5').text
            article_url = news_block.find('h5').find('a')['href']
            article_content = news_block.find('h5').find_next('p').text.strip()
            article_date = self.parse_date(date)

            if article_date and article_date.date() == datetime.now().date():
                translated_title = self.translate_text(article_title)
                translated_content = self.translate_text(article_content)

                article = {
                    '이미지_경로': image_url,
                    '제목': translated_title,
                    '내용': translated_content,
                    'Link': article_url,
                    '작성일자': article_date.strftime("%Y.%m.%d %H:%M")
                }
                articles.append(article)

        return articles

    def send_to_slack(self, articles):
        slack_token = '*'
        client = WebClient(token=slack_token)
        channel = 'C063YJKGJA3'

        for article_item in articles:
            try:
                formatted_date = article_item.get('작성일자')
                message = {
                    "blocks": [
                        {"type": "divider"},
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"{article_item.get('제목', '')}",
                                "emoji": True
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"{article_item.get('내용', '')}\n{article_item.get('Link', '')}\n{formatted_date}"
                            },
                            "accessory": {
                                "type": "image",
                                "image_url": f"{article_item.get('이미지_경로', '')}",
                                "alt_text": "Image"
                            }
                        },
                        {"type": "divider"}
                    ]
                }

                response = client.chat_postMessage(channel=channel, blocks=message['blocks'])
                print(response)

            except Exception as e:
                print(f"Slack으로의 발송 중 에러 발생: {str(e)}")

if __name__ == "__main__":
    scraper = NewsScraper()
    while True:
        print(f"현재 수집 중인 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        articles = scraper.scrape_news_articles()

        for article in articles:
            print(f"◈제목: {article.get('제목', '')}\n◈내용: {article.get('내용', '')}\n◈Link: {article.get('Link', '')}\n◈작성일자: {article.get('작성일자', '')}\n")

        scraper.send_to_slack(articles)
        time.sleep(3600)
