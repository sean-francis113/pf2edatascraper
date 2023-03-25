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
            equipment_description = ""

            full_url = f"https://2e.aonprd.com/{url}?ID={i}"

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
            
            sub_header_list = container.find_all("h2")
            
            if(len(sub_header_list) > 0):
                
                trait_spans = container.find_all(_class="trait")
                trait_str = ""

                if len(trait_spans) > 0:
                    for trait in trait_spans:
                        trait_str += trait.text + ","
                    if(trait_str[-1] == ","):
                        trait_str = trait_str[:-1]

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
                
                hr_pos = html.find("<hr>", html.find("ctl00_RadDrawer1_Content_MainContent_DetailedOutput"))
                equipment_description = html[hr_pos + len("<hr>"):find_earliest_position(html.find("<hr>", hr_pos), html.find("<br>", hr_pos))]
                equipment_description = remove_tags(equipment_description)
                
                bulk_start_pos = html.find("<b>Bulk</b>")
                bulk_end_pos = find_earliest_position(html.find(";", bulk_start_pos), html.find("\n", bulk_start_pos), html.find("<br>", bulk_start_pos), html.find("<hr>", bulk_start_pos))
                
                equipment_bulk = html[bulk_start_pos + len("<b>Bulk</b>"):bulk_end_pos].strip()

                equipment_category = url[:url.find(".")]
                
                for h in sub_header_list:
                    equipment_name_level_str = remove_tags(h.text)
                    
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
                        
                    price_start_pos = html.find("<b>Price</b>", html.find(equipment_name))
                    price_end_pos = find_earliest_position(html.find(";", price_start_pos), html.find("\n", price_start_pos), html.find("<br>", price_start_pos), html.find("<hr>", price_start_pos))

                    equipment_price = html[price_start_pos + len("<b>Price</b>"):price_end_pos].strip()
                    
                    equipment_description_start = html.find("<br>", price_end_pos) + len("<br>")
                    equipment_description_end = find_earliest_position(html.find(";", equipment_description_start), html.find("\n", equipment_description_start), html.find("<br>", equipment_description_start), html.find("<hr>", equipment_description_start))
                
                    equipment_description_temp = "\n" + html[equipment_description_start:equipment_description_end]
                
                    equipment_output.append([equipment_name, full_url, equipment_traits, equipment_category, equipment_level, equipment_price, equipment_bulk, equipment_description + "\n" + equipment_description_temp])
                
            else:
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

                trait_spans = container.find_all(_class="trait")
                trait_str = ""

                if len(trait_spans) > 0:
                    for trait in trait_spans:
                        trait_str += trait.text + ","
                    if(trait_str[-1] == ","):
                        trait_str = trait_str[:-1]

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
            
def organize_equipment_data():
    log("Getting Equipment Data")
    output = grab_equipment_data()

    organized_output = []

    log("Organizing Equipment Data")
    for equipment in output:
        log(f"Adding \"{equipment[0]}\",\"{equipment[1]}\",\"{equipment[2]}\",\"{equipment[3]}\",\"{equipment[4]}\",\"{equipment[5]}\",\"{equipment[6]}\" to Organzied Output")
        organized_output.append(f"\"{equipment[0]}\",\"{equipment[1]}\",\"{equipment[2]}\",\"{equipment[3]}\",\"{equipment[4]}\",\"{equipment[5]}\",\"{equipment[6]}\"")

    return organized_output
