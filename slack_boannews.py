import slack_sdk
from slack_sdk import WebClient
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from datetime import datetime, timedelta
import time
import certifi
import warnings
from urllib3.exceptions import InsecureRequestWarning

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
        self.wait = WebDriverWait(self.driver, 10)

    def parse_date(self, date_str):
        try:
            date_str = date_str.split("|")[-1].strip()
            return datetime.strptime(date_str, "%Y년 %m월 %d일 %H:%M")
        except ValueError:
            print(f"날짜 형식이 일치하지 않습니다: {date_str}")
            return datetime.now()

    def scrape_news_articles(self):
        url = "https://www.boannews.com/media/t_list.asp"
        self.driver.get(url)

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        news_list = soup.select('.news_list')

        articles = []

        for news_item in news_list:
            title_element = news_item.select_one('.news_txt')
            title = title_element.text.strip()

            content_element = news_item.select_one('.news_content')
            content = content_element.text.strip()

            link_element = title_element.find_parent('a')
            link = link_element['href']

            date_element = news_item.select_one('.news_writer')
            date_str = date_element.text.strip()

            article_date = self.parse_date(date_str)
            if article_date and datetime.now() - article_date < timedelta(minutes=30):
                article = {
                    '제목': title,
                    '내용': content,
                    'Link': 'https://www.boannews.com/'+link,
                    '작성일자': article_date.strftime("%Y.%m.%d %H:%M")
                }
                articles.append(article)
                #self.send_to_slack(article)

        return articles

    def send_to_slack(self, articles):
        slack_token = '*'
        client = WebClient(token=slack_token)

        for article_item in articles:
            try:
                formatted_date = article_item.get('작성일자')
                message = f"제목: {article_item.get('제목', '')}\n내용: {article_item.get('내용', '')}\nLink: {article_item.get('Link', '')}\n작성일자: {formatted_date}\n"

                response = client.chat_postMessage(channel='C064RQ44EF3', text=message)
                print(response)
            except Exception as e:
                print(f"Slack으로의 발송 중 에러 발생: {str(e)}")


    # def run_continuously(self):
    #     while True:
    #         print(f"현재 수집 중인 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    #         articles = self.scrape_news_articles()
    #
    #         for article in articles:
    #             print(f"제목: {article.get('제목', '')}\n내용: {article.get('내용', '')}\nLink: {article.get('Link', '')}\n작성일자: {article.get('작성일자', '')}\n")
    #
    #         self.send_to_slack(articles)
    #         time.sleep(1800)

if __name__ == "__main__":
    scraper = NewsScraper()
    while True:
        print(f"현재 수집 중인 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        articles = scraper.scrape_news_articles()

        for article in articles:
            print(f"제목: {article.get('제목', '')}\n내용: {article.get('내용', '')}\nLink: {article.get('Link', '')}\n작성일자: {article.get('작성일자', '')}\n")

        scraper.send_to_slack(articles)
        time.sleep(1800)
