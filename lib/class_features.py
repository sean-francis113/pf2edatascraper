from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time

import lib.db
from lib.helper import remove_tags, find_earliest_position, open_selenium
from lib.log import log_text as log

url = "https://2e.aonprd.com/Classes.aspx"

def upload_features_data():
    log("Starting Class Feature Upload Preperation")
    features_data = organize_features_data()
    log("Preparation Done")

    log("Clearing Table")
    conn, row_count, result = lib.db.query_database("DELETE FROM official_class_features;", get_result=True, close_conn=False)

    log("Starting INSERT Process")
    for feature in features_data:
        log("Inserting " + feature + " Into Database")
        conn = lib.db.query_database("INSERT INTO official_class_features VALUES (" + feature + ");", connection=conn, close_conn=False)[0]

    log("Commiting Database Changes")
    conn.commit()
    log("Closing Connection")
    conn.close()

def grab_feature_data():
    feature_output = []

    driver = open_selenium()
    log("Going to Page: " + url)
    driver.get(url)
    log("Waiting for Page to Load")
    time.sleep(5)

    log("Getting Page Source")
    html = driver.page_source
    log("Setting up BeautifulSoup with Source")
    soup = BeautifulSoup(html, "html.parser")

    log("Finding Initial HTML Container")
    container = soup.find(id="ctl00_RadDrawer1_Content_MainContent_Navigation")
    log("Finding All Categories in Container")
    name_list = container.find_all("h1")

    for item in name_list:
        log("Getting All Links in Category")
        links = item.find_all("a")

        log("Grabbing Classes from Links")
        for link in links:

            if link.get("href").startswith("Classes.aspx"):
                class_name = link.text
                class_link = "https://2e.aonprd.com/" + link.get("href")
                log("Found " + class_name + " With the Following Link: " + class_link)

                log("Opening Class Page")
                class_driver = open_selenium()
                class_driver.get(class_link)
                log("Waiting for Page to Load")
                time.sleep(5)

                log("Getting Class Page Source")
                class_html = class_driver.page_source
                log("Preparing BeautifulSoup for Page Source")
                class_soup = BeautifulSoup(class_html, "html.parser")

                log("Finding Class Features Heading")
                feature_h1_pos = class_html.find("Class Features</h1>")

                log("Grabbing All h2 Headings")
                h2_headings = class_soup.find_all("h2")
                feature_name = ""
                feature_level = ""
                feature_summary = ""
                found_feature = False
                found_feature_pos = class_html.find("<h1 class=\"title\">Class Features</h1>")
                x = 0

                log("Searching Through Headings for Features")
                for h in h2_headings:
                    if h.text == "Ancestry and Background":
                        found_feature = True
                    if found_feature == True:
                        full_feature_name = h.text
                        if full_feature_name.find("Level ") != -1:
                            feature_name = full_feature_name[:full_feature_name.find("Level ")]
                            feature_level = full_feature_name[full_feature_name.find("Level ") + len("Level "):]
                            feature_level = int(feature_level)
                        else:
                            feature_name = h.text
                            feature_level = 1

                        duplicate_feature = False
                        for feature in feature_output:
                            if feature[0] == feature_name:
                                duplicate_feature = True
                                break

                        if duplicate_feature == True:
                            continue

                        find_str = ">" + feature_name + "</h2>"
                        start_pos = class_html.find(find_str, found_feature_pos) + len(find_str)
                        if start_pos == len(find_str)-1:
                            find_str = "<h2 class=\"title\">" + feature_name + "<span "
                            temp_pos = class_html.find(find_str, found_feature_pos)
                            start_pos = class_html.find("</h2>", temp_pos) + len("</h2>")
                        h3_pos = class_html.find("<h3", start_pos)
                        h2_pos = class_html.find("<h2", start_pos)
                        span_pos = class_html.find("<span", start_pos)
                        span_close_pos = class_html.find("</span>", start_pos)

                        end_pos = find_earliest_position(h3_pos, h2_pos, span_pos, span_close_pos)

                        feature_summary = class_html[start_pos:end_pos]
                        if feature_summary.endswith("<br>"):
                            feature_summary = feature_summary[:-len("<br>")]

                        feature_summary = feature_summary.replace("<br>", "\n")
                        feature_summary = remove_tags(feature_summary, tag_to_remove="h2", remove_inside=True)
                        feature_summary = remove_tags(feature_summary, tag_to_remove="table", remove_inside=True)
                        feature_summary = remove_tags(feature_summary, tag_to_remove="i")
                        feature_summary = remove_tags(feature_summary, tag_to_remove="u")
                        feature_summary = remove_tags(feature_summary, tag_to_remove="b")
                        feature_summary = remove_tags(feature_summary, tag_to_remove="a")

                        log(str([feature_name, feature_level, feature_summary]))
                        feature_output.append([feature_name, feature_level, feature_summary])

    return feature_output

def organize_features_data():
    log("Getting Feature Data")
    output = grab_feature_data()

    organized_output = []

    for feature in output:
        log(f"Adding \"{feature[0]}\",{feature[1]},\"{feature[2]}\" to Organzied Output")
        organized_output.append(f"\"{feature[0]}\",{feature[1]},\"{feature[2]}\"")

    return organized_output
