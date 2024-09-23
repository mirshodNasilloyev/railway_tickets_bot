import time
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from data import db


class WebDriverHandler:
    def __init__(self):
        self.driver = None

    def setup_driver(self, url: str):
        chrome_option = Options()
        chrome_option.add_argument('--no-sandbox')
        chrome_option.add_argument('--headless')
        chrome_option.add_argument('--disable-dev-5shm-usage')
        self.driver = webdriver.Chrome(options=chrome_option)
        self.driver.get(url)
        self.driver.implicitly_wait(10)

    def stop_driver(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

    def run_driver(self, xpath_list: list):
        for i in xpath_list:
            self.driver.find_element(By.XPATH, value=i).click()
            time.sleep(1)

    def data_handling(self):
        data: dict = {
            'train_brand': None,
            'time_dep': None,
            'dep_station': None,
            'time_arr': None,
            'arr_station': None,
        }

        html_content = self.driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        trains_div = soup.find_all('div', class_='trains__list mb-4')
        for div in trains_div:
            if div is not None:
                items = [div.find('div', class_=f'{i}').get_text() for i in data.keys()]
                db.append(items)
            else:
                print('Other keys elements is Null')


