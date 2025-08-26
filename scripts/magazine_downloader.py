import datetime
import time
from datetime import timedelta

from selenium import webdriver
import re
from bs4 import BeautifulSoup

MONTH_ENGLISH = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December"
]


def download_magazine_list():
    driver = webdriver.Chrome()

    for i in range(34, 41):
        url = f'https://magazinelib.com/page/{i}/?s=the+economist'
        driver.get(url)
        time.sleep(30 + i)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        print(f"### Page {i:02d} ###")
        for item in soup.find_all('a'):
            href = item.get('href')
            if not href.startswith("https://magazinelib.com/all/the-economist-"):
                continue
            print(item.get('href'))


def clean_magazine_url():
    path = './assets/the_economist/url_list.txt'
    urls = open(path, 'r').read().split('\n')
    urls = list(set(urls))
    urls.sort(reverse=True)
    cursor = datetime.datetime.now().date()
    dates_available = set()
    cleaned_url = []
    while True:
        cursor = cursor - timedelta(days=1)
        if (cursor + timedelta(days=1)).isoformat() in dates_available:
            continue
        cur_date = cursor.isoformat()
        if cur_date < '2022-07-02':
            break
        year, month, day = cursor.year, MONTH_ENGLISH[cursor.month - 1].lower(), cursor.day
        candidates = [x for x in urls if f'{month}-{day}-{year}' in x] + [x for x in urls if
                                                                          f'-{day}-{month}-{year}/' in x]
        if not candidates:
            continue
        cleaned_url.append(candidates[0])
        dates_available.add(cur_date)
    for item in cleaned_url:
        print(item)
    print(len(cleaned_url))


def download_magazine_pdf():
    driver = webdriver.Chrome()
    path = './assets/the_economist/cleaned_url_list.md'
    urls = open(path, 'r').read().split('\n')

    for url in urls:
        driver.get(url)
        while len(driver.window_handles) > 0:
            time.sleep(1)
        break


if __name__ == '__main__':
    download_magazine_pdf()
