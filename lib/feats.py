from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

import lib.db
from lib.helper import remove_tags, find_earliest_position, find_which_exists
from lib.log import log_text as log

feat_url = "https://2e.aonprd.com/Feats.aspx?ID="
error_limit = 5
test_limit = 0

def upload_feat_data():
    log("Starting Feat Upload Preperation")
    feat_data = organize_feat_data()
    log("Preparation Done")

    log("Clearing Table")
    conn, row_count, result = lib.db.query_database("DELETE FROM official_feats;", get_result=True, close_conn=False)

    log("Starting INSERT Process")
    for feat in feat_data:
        log("Inserting " + feat + " Into Database")
        conn = lib.db.query_database("INSERT INTO official_feats VALUES (" + feat + ");", connection=conn, close_conn=False)[0]

    log("Commiting Database Changes")
    conn.commit()
    log("Closing Connection")
    conn.close()
    
def grab_feat_data():
    global error_limit
    curr_error_num = 0

    feat_output = []

    log("Starting to Grab Feats")

    i = 1

    while(True):
        feat_name = ""
        feat_link = f"{feat_url}{i}"
        feat_level = ""
        feat_summary = ""

        log("Opening Browser")
        driver = webdriver.Chrome('./chromedriver.exe')
        log(f"Going to Page: {feat_link}")
        driver.get(f"{feat_link}")
        #log("Waiting for Page to Load")
        #time.sleep(5)

        log("Getting Page Source")
        html = driver.page_source

        if html.find("Server Error in '/' Application.") > -1:
            log("Reached An Unknown Feat ID.")
            curr_error_num += 1
            if curr_error_num == error_limit:
                log("Ending Search.")
                break
            else:
                log(f"Reached Unknown Feat {curr_error_num} in a Row. Limit is {error_limit}")
                i += 1
                continue

        if curr_error_num > 0:
            log("Resetting Error Count")
            curr_error_num = 0

        log("Setting up BeautifulSoup with Source")
        soup = BeautifulSoup(html, "html.parser")

        log("Finding Feat Name and Level")
        container = soup.find(id="ctl00_RadDrawer1_Content_MainContent_DetailedOutput")
        feat_name_level = container.find("h1")
        feat_name_level_pos = html.find("ctl00_RadDrawer1_Content_MainContent_DetailedOutput")
        print(feat_name_level_pos)
        feat_name_level_str = feat_name_level.text

        feat_name = feat_name_level_str[:feat_name_level_str.find("Feat")]
        feat_level = feat_name_level_str[feat_name_level_str.find("Feat"):].split(" ")[1]

        log(f"Found: {feat_name}, Level {feat_level}")

        log("Finding Feat Summary")
        summary_start_pos = html.find("<hr>", feat_name_level_pos) + len("<hr>")
        summary_end_pos = find_earliest_position(html.find("<br>", summary_start_pos),html.find("<hr>", summary_start_pos),html.find("<span", summary_start_pos),html.find("<h2", summary_start_pos), html.find("<h3", summary_start_pos),html.find("<ul", summary_start_pos),html.find("</span>", summary_start_pos))

        feat_summary = html[summary_start_pos:summary_end_pos]

        log(f"Found: {feat_summary}")
        feat_summary = remove_tags(feat_summary, tag_to_remove="h2", remove_inside=True)
        feat_summary = remove_tags(feat_summary, tag_to_remove="table", remove_inside=True)
        feat_summary = remove_tags(feat_summary, tag_to_remove="i")
        feat_summary = remove_tags(feat_summary, tag_to_remove="u")
        feat_summary = remove_tags(feat_summary, tag_to_remove="b")
        feat_summary = remove_tags(feat_summary, tag_to_remove="a")
        
        if feat_summary.endswith("\n"):
            feat_summary[:-2]

        feat_output.append([feat_name, feat_link, feat_level, feat_summary])
        log([feat_name, feat_link, feat_level, feat_summary])

        if(test_limit > 0 and i == test_limit):
            break
        i += 1

    return feat_output

def organize_feat_data():
    log("Getting Feat Data")
    feat_output = grab_feat_data()
    organized_output = []
    log("Starting to Organize Data")

    for f in feat_output:
        log(f"Adding {f} to Organized Output String")
        organized_output.append(f"\"{f[0]}\", \"{f[1]}\", \"{f[2]}\", \"{f[3]}\"")
        log(f"Added \"{f[0]}\", \"{f[1]}\", \"{f[2]}\", \"{f[3]}\" to Organized Output")

    return organized_output