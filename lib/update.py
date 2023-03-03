from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import os
import datetime
from os.path import exists
from datetime import date

import lib.db
from lib.helper import open_selenium
from lib.log import log_text as log

update_file_path = "./update.txt"
update_file = None
latest_update_time = ""

def open_update_file(file_mode = "a"):
    global update_file

    print("Trying to Open Update File \"" + update_file_path + "\"")

    if update_file is not None and check_file_status() == False:
        update_file.close()

    if exists(update_file_path):
        update_file = open(update_file_path, file_mode)
        return update_file
    else:
        f = open(update_file_path, "x")
        f.close()
        update_file = open(update_file_path, file_mode)
        return update_file

def check_for_update():
    global update_file
    text_lines = []
    
    update_file = open_update_file("r")
    text_lines = update_file.readlines()
    
    if len(text_lines) == 0:
        update_file.close()
        return True
    else:
        url = "https://2e.aonprd.com"
        
        log("Opening Browser")
        driver = open_selenium()
        log("Going to Page: " + url)
        driver.get(url)

        log("Getting Page Source")
        html = driver.page_source
        log("Setting up BeautifulSoup with Source")
        soup = BeautifulSoup(html, "html.parser")

        log("Finding Initial HTML Container")
        container = soup.find(id="ctl00_RadDrawer1_Content_MainContent_MainNewsFeed")
        log("Finding All Categories in Container")
        name_list = container.find_all("h1")
        
        if name_list[0] != text_lines[0]:
            update_file.close()
            return True
        else:
            update_file.close()
            return False
    
def set_update_time():
    update_file = open_update_file("w")
    
    if latest_update_time != "":
        update_file.write(latest_update_time)
        update_file.close()
        return
    else:
        url = "https://2e.aonprd.com"
        
        log("Opening Browser")
        driver = open_selenium()
        log("Going to Page: " + url)
        driver.get(url)

        log("Getting Page Source")
        html = driver.page_source
        log("Setting up BeautifulSoup with Source")
        soup = BeautifulSoup(html, "html.parser")

        log("Finding Initial HTML Container")
        container = soup.find(id="ctl00_RadDrawer1_Content_MainContent_MainNewsFeed")
        log("Finding All Categories in Container")
        name_list = container.find_all("h1")
        
        update_file.write(name_list[0])
        update_file.close()
        return

def check_file_status():
    try:
        os.rename(update_file_path, update_file_path)
        return True #File is Closed
    except OSError:
        return False #File is Open