from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time

import lib.db
from lib.helper import remove_tags
from lib.log import log_text as log

url = "https://2e.aonprd.com/Backgrounds.aspx?ID="
test_limit = 0
error_limit = 5

def upload_background_data():
    log("Starting Background Upload Preperation")
    background_data = organize_background_data()
    log("Preparation Done")

    log("Clearing Table")
    conn, row_count, result = lib.db.query_database("DELETE FROM official_backgrounds;", get_result=True, close_conn=False)

    log("Starting INSERT Process")
    for background in background_data:
        log("Inserting " + background + " Into Database")
        conn = lib.db.query_database("INSERT INTO official_backgrounds VALUES (" + background + ");", connection=conn, close_conn=False)[0]

    log("Commiting Database Changes")
    conn.commit()
    log("Closing Connection")
    conn.close()

def grab_background_data():
    global error_limit
    curr_error_num = 0

    background_output = []

    log("Starting to Grab Backgrounds")

    i = 0

    while(True):
        background_name = ""
        background_link = f"{url}{i}"
        background_summary = ""

        log("Opening Browser")
        driver = webdriver.Chrome('./chromedriver.exe')
        log(f"Going to Page: {url}{i}")
        driver.get(f"{url}{i}")
        #log("Waiting for Page to Load")
        #time.sleep(5)

        log("Getting Page Source")
        html = driver.page_source

        if html.find("Server Error in '/' Application.") > -1:
            log("Reached An Unknown Background ID.")
            curr_error_num += 1
            if curr_error_num == error_limit:
                log("Ending Search.")
                break
            else:
                log(f"Reached Unknown Background {curr_error_num} in a Row. Limit is {error_limit}")
                i += 1
                continue

        if curr_error_num > 0:
            log("Resetting Error Count")
            curr_error_num = 0

        log("Setting up BeautifulSoup with Source")
        soup = BeautifulSoup(html, "html.parser")

        log("Using Links to Find Background Name")
        container = soup.find(id="ctl00_RadDrawer1_Content_MainContent_DetailedOutput")
        links = container.find_all("a")

        for link in links:
            if link.get("href") == f"Backgrounds.aspx?ID={i}":
                log(f"Found: {link.text}")
                background_name = link.text

                log("Finding Background Summary")
                start_pos = html.find("<br>", link.sourcepos) + len("<br>")
                second_br_pos = html.find("<br>", start_pos) + len("<br>")

                if html.find("<b>Source</b>", start_pos, second_br_pos) > -1:
                    start_pos = second_br_pos

                end_pos = html.find("</span>", start_pos)

                if html.find("<span ", start_pos, end_pos):
                    end_pos = html.rfind("<br>", start_pos, end_pos)

                background_summary = html[start_pos:end_pos].strip()
                log(f"Found: {background_summary}")
                background_summary = background_summary.replace("<br>", "\n")
                background_summary = remove_tags(background_summary, tag_to_remove="h2", remove_inside=True)
                background_summary = remove_tags(background_summary, tag_to_remove="table", remove_inside=True)
                background_summary = remove_tags(background_summary, tag_to_remove="i")
                background_summary = remove_tags(background_summary, tag_to_remove="u")
                background_summary = remove_tags(background_summary, tag_to_remove="b")
                background_summary = remove_tags(background_summary, tag_to_remove="a")

                background_output.append([background_name, background_link, background_summary])
                log(str([background_name, background_link, background_summary]))
                break

        if(test_limit > 0 and i == test_limit):
            break
        i += 1

    return background_output

def organize_background_data():
    log("Getting Background Data")
    output = grab_background_data()

    organized_data = []

    log("Starting to Organize Background Data")
    for background in output:
        summary = background[2].replace("\"", "\'")
        organized_data.append(f"\"{background[0]}\", \"{background[1]}\", \"{summary}\"")
        log(f"Added \"{background[0]}\", \"{background[1]}\", \"{summary}\" to Organized Data")

    return organized_data
