from os import remove
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time

import lib.db
from lib.helper import remove_tags, find_earliest_position, find_which_exists, open_selenium
from lib.log import log_text as log

url = "https://2e.aonprd.com/Equipment.aspx"
test_limit = 0
error_limit = 5

def upload_equipment_data():
    log("Starting Equipment Upload Preperation")
    equipment_data = organize_equipment_data()
    log("Preparation Done")

    log("Clearing Table")
    conn, row_count, result = lib.db.query_database("DELETE FROM official_equipment;", get_result=True, close_conn=False)

    log("Starting INSERT Process")
    for equipment in equipment_data:
        log("Inserting " + equipment + " Into Database")
        conn = lib.db.query_database("INSERT INTO official_equipment VALUES (" + equipment + ");", connection=conn, close_conn=False)[0]

    log("Commiting Database Changes")
    conn.commit()
    log("Closing Connection")
    conn.close()

def grab_equipment_data():
    global error_limit

    equipment_output = []
    link_list = ["Equipment.aspx", "Vehicles.aspx", "Weapons.aspx", "Armor.aspx", "Shields.aspx"]

    driver = open_selenium()

    if driver == None: return

    x = 0
    
    for url in link_list:
        i = 1
        curr_error_num = 0

        while(True):
            equipment_name = ""
            equipment_traits = ""
            equipment_category = ""
            equipment_level = ""
            equipment_price = ""
            equipment_bulk = ""

            full_url = f"https://2e.aonprd.com/{url}?ID={i}"

            log("Opening Browser")
            driver = open_selenium()
            log(f"Going to Page: {full_url}")
            driver.get(f"{full_url}")

            log("Getting Page Source")
            html = driver.page_source
            
            if html.find("Server Error in '/' Application.") > -1:
                log("Reached An Unknown Equipment ID.")
                curr_error_num += 1
                if curr_error_num == error_limit:
                    log("Ending Search. Moving to Next Equipment Category.")
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

            log("Finding Equipment Name and Level")
            container = soup.find(id="ctl00_RadDrawer1_Content_MainContent_DetailedOutput")
            equipment_name_level = container.find("h1")
            equipment_name_level_pos = html.find("ctl00_RadDrawer1_Content_MainContent_DetailedOutput")
            print(equipment_name_level_pos)
            equipment_name_level_str = equipment_name_level.text

            if equipment_name_level_str.find("Item") > -1:
                equipment_name = equipment_name_level_str[:equipment_name_level_str.find("Item")]
                equipment_level = equipment_name_level_str[equipment_name_level_str.find("Item"):].split(" ")[1]

                log(f"Found: {equipment_name}, Level {equipment_level}")
            elif equipment_name_level_str.find("Vehicle") > -1:
                equipment_name = equipment_name_level_str[:equipment_name_level_str.find("Vehicle")]
                equipment_level = equipment_name_level_str[equipment_name_level_str.find("Vehicle"):].split(" ")[1]

                log(f"Found: {equipment_name}, Level {equipment_level}")
            else:
                equipment_name = equipment_name_level_str
                log(f"Found: {equipment_name}")

            trait_spans = container.find_all(By.CLASS_NAME, "trait")
            trait_str = ""

            if len(trait_spans) > 0:
                for trait in trait_spans:
                    trait_str += trait.text

            elif(html.find("<b>Traits</b>") > -1):
                trait_start_pos = 0
                trait_start_pos = html.find("<b>Traits</b>") + len("<b>Traits</b>")
                trait_end_pos = find_earliest_position(html.find("<br>", trait_start_pos), html.find("<hr>", trait_start_pos), html.find(";", trait_start_pos))
                trait_str = html[trait_start_pos:trait_end_pos]

                trait_str = remove_tags(trait_str, "u")
                trait_str = remove_tags(trait_str, "a")
            else:
                trait_str = "-"

            equipment_traits = trait_str.strip()

            price_start_pos = html.find("<b>Price</b>")
            price_end_pos = find_earliest_position(html.find(";", price_start_pos), html.find("\n", price_start_pos), html.find("<br>", price_start_pos), html.find("<hr>", price_start_pos))

            equipment_price = html[price_start_pos + len("<b>Price</b>"):price_end_pos].strip()

            bulk_start_pos = html.find("<b>Bulk</b>")
            bulk_end_pos = find_earliest_position(html.find(";", bulk_start_pos), html.find("\n", bulk_start_pos), html.find("<br>", bulk_start_pos), html.find("<hr>", bulk_start_pos))

            equipment_bulk = html[bulk_start_pos + len("<b>Bulk</b>"):bulk_end_pos].strip()

            equipment_category = url[:url.find(".")]

            equipment_output.append([equipment_name, full_url, equipment_traits, equipment_category, equipment_level, equipment_price, equipment_bulk])

            x += 1
            i += 1
            if test_limit > 0 and x == test_limit:
                break

        if test_limit > 0 and x == test_limit:
            break
            
    log(f"Equipment Output: {equipment_output}")
    return equipment_output

#    log("Finding Table")
#    container = soup.find("table", _class="column gap-medium")
#    
#    log("Getting Table Body")
#    table_body = container.find("tbody")
#    
#    log("Getting Table Rows")
#    table_rows = table_body.find_all("tr")
#    
#    ignore_col = [2, 3, 4, 6, 10]
#    
#    i = 1
#    get_link = True
#    x = 1
#    
#    log("Looking Through Rows for Data")
#    for row in table_rows:
#        row_data = row.find_all("td")
#        data_output = []
#        for data in row_data:
#            if i in ignore_col:
#                log(f"Ignoring Column {i}")
#                i += 1
#                continue
#            
#            data_text = data.text.replace("\n", "")
#            log(f"Found: {data_text}")
#            data_output.append(data_text)
#            
#            if get_link:
#                links = data.find_all("a")
#                for l in links:
#                    for s in link_list:
#                        if l.get("href").startswith(s):
#                            data_output.append("https://2e.aonprd.com/" + l.get("href"))
#                            get_link = False
#            
#            i += 1
#        
#        log(f"Data Output: {data_output}")    
#        equipment_output.append(data_output)
#        i = 1
#        get_link = True
            
def organize_equipment_data():
    log("Getting Equipment Data")
    output = grab_equipment_data()

    organized_output = []

    log("Organizing Equipment Data")
    for equipment in output:
        log(f"Adding \"{equipment[0]}\",\"{equipment[1]}\",\"{equipment[2]}\",\"{equipment[3]}\",\"{equipment[4]}\",\"{equipment[5]}\",\"{equipment[6]}\" to Organzied Output")
        organized_output.append(f"\"{equipment[0]}\",\"{equipment[1]}\",\"{equipment[2]}\",\"{equipment[3]}\",\"{equipment[4]}\",\"{equipment[5]}\",\"{equipment[6]}\"")

    return organized_output
