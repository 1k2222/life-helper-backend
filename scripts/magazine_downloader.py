import datetime
import glob
import os
import time
from datetime import timedelta
from os import makedirs
import shutil

from selenium import webdriver
from bs4 import BeautifulSoup

from scripts.defines import MONTH_ENGLISH


def download_magazine_list():
    driver = webdriver.Chrome()

    for i in range(18, 23):
        url = f'https://magazinelib.com/page/{i}/?s=the+economist'
        driver.get(url)
        time.sleep(30)
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
        if cur_date < '2022-01-01':
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


def rename_pdf():
    src_dir = './assets/the_economist/raw_pdfs'
    src_file_pattern = os.path.join(src_dir, '*.pdf')
    dest_dir = './assets/the_economist/pdfs'
    src_files = glob.glob(src_file_pattern)
    makedirs(dest_dir, exist_ok=True)
    cursor = datetime.datetime.now().date()
    missed_pdfs = set(src_files)
    while True:
        cursor = cursor - timedelta(days=1)
        cur_date = cursor.isoformat()
        if cur_date < '2022-01-01':
            break
        year, month, day = cursor.year, MONTH_ENGLISH[cursor.month - 1], cursor.day
        candidates = [x for x in src_files if f'_{month}_{day}_{year}.pdf' in x] + [x for x in src_files if
                                                                                    f'_{day}_{month}_{year}.pdf' in x]
        assert len(candidates) <= 1
        if candidates:
            candidates = candidates[0]
            missed_pdfs.remove(candidates)
            dest_file = os.path.join(dest_dir, f'The_Economist_{cur_date.replace('-', '_')}.pdf')
            shutil.copy(candidates, dest_file)
    for item in missed_pdfs:
        print(item)
    print(len(missed_pdfs))


if __name__ == '__main__':
    rename_pdf()
