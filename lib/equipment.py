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
    skip_list = ["https://2e.aonprd.com/Weapons.aspx?ID=1", "https://2e.aonprd.com/Armor.aspx?ID=1"]

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
            
            if(full_url in skip_list): 
                i += 1
                continue

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
            header_index = 0
            
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
            
            while(header_index < len(sub_header_list)):
                if("may contain spoilers" in str(sub_header_list[header_index]) or equipment_name not in str(sub_header_list[header_index])):
                    del sub_header_list[header_index]
                    header_index = 0
                    continue
                header_index += 1
            
            #for header in sub_header_list:
                #if("may contain spoilers" in str(header)):
                    #del sub_header_list[header_index]
                    #break
                
                #header_index += 1
            
            if(len(sub_header_list) > 0):
                log("Found Multiple Versions of Equipment")
                
                trait_spans = container.find_all("span", {"class": "trait"})
                trait_uncommon = container.find({"class": "traituncommon"})
                trait_rare = container.find({"class": "traitrare"})
                trait_str = ""
                
                if(trait_rare != None):
                    trait_str += "Rare, "
                if(trait_uncommon != None):
                    trait_str += "Uncommon, "

                if len(trait_spans) > 0:
                    for trait in trait_spans:
                        trait_str += trait.text + ", "
                    if(trait_str[-1] == ","):
                        trait_str = trait_str[:-1]
                    elif(trait_str[-2:-1] == ", "):
                        trait_str = trait_str[:-2]
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
                
                log(f"Traits: {equipment_traits}")
                
                hr_pos = html.find("<hr>", html.find("ctl00_RadDrawer1_Content_MainContent_DetailedOutput"))
                print(f"HR POS: {hr_pos}")
                equipment_description = html[hr_pos + len("<hr>"):find_earliest_position(html.find("<hr>", hr_pos + 1), html.find("<h2", hr_pos + 1), html.find("</span>", hr_pos + 1))]
                equipment_description = remove_tags(equipment_description)
                
                while(equipment_description.lower().find("nethys note") > -1):
                    note_pos = equipment_description.lower().find("nethys note")
                    note_end = equipment_description.lower().find(".", note_pos) + 1
                    equipment_description = equipment_description.replace(equipment_description[note_pos:note_end], "").strip()
                
                log(f"Description: {equipment_description}")
                
                bulk_start_pos = html.find("<b>Bulk</b>")
                bulk_end_pos = find_earliest_position(html.find(";", bulk_start_pos), html.find("\n", bulk_start_pos), html.find("<br>", bulk_start_pos), html.find("<hr>", bulk_start_pos))
                
                equipment_bulk = html[bulk_start_pos + len("<b>Bulk</b>"):bulk_end_pos].strip()
                
                log(f"Bulk: {equipment_bulk}")

                equipment_category = url[:url.find(".")]
                
                for h in sub_header_list:
                    
                    if str(h).find("class=\"title\"") == -1: continue
                    
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
                    
                    log(f"Price: {equipment_bulk}")
                    
                    #equipment_description_start = html.find("<br>", price_end_pos) + len("<br>")
                    #equipment_description_end = find_earliest_position(html.find(";", equipment_description_start), html.find("\n", equipment_description_start), html.find("<br>", equipment_description_start), html.find("<hr>", equipment_description_start))
                
                    desc_search_heading = html.find(equipment_name, hr_pos)
                    print(f"Search Heading: {desc_search_heading}")
                    desc_search_start = html.find("</h2>", desc_search_heading) + len("</h2>")
                    desc_search_end = find_earliest_position(html.find("</span>", desc_search_start), html.find("<h2", desc_search_start))
                    
                    full_search = html[desc_search_start:desc_search_end]
                    print(str(h))
                    print(f"Full Search: {full_search}")
                    split_search = full_search.split("<br>")
                
                    equipment_description_temp = ""
                    
                    for line in split_search:
                        if(line.startswith("<b>")): continue
                        
                        equipment_description_temp += f"{line}\n\n"
                        
                    equipment_description_temp = remove_tags(equipment_description_temp)
                    while(equipment_description.lower().find("nethys note") > -1):
                        note_pos = equipment_description_temp.lower().find("nethys note")
                        note_end = equipment_description_temp.lower().find(".", note_pos) + 1
                        equipment_description_temp = equipment_description_temp.replace(equipment_description_temp[note_pos:note_end], "").strip()
                    equipment_description_temp = equipment_description_temp.strip()
                    
                    log(f"Description Addition: {equipment_description_temp}")
                
                    equipment_output.append([equipment_name, full_url, equipment_traits, equipment_category, equipment_level, equipment_price, equipment_bulk, (equipment_description + "\n\n" + equipment_description_temp).strip()])
                
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

                trait_spans = container.find_all("span", {"class": "trait"})
                trait_uncommon = container.find({"class": "traituncommon"})
                trait_rare = container.find({"class": "traitrare"})
                trait_str = ""
                
                if(trait_rare != None):
                    trait_str += "Rare, "
                if(trait_uncommon != None):
                    trait_str += "Uncommon, "

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
                
                log(f"Traits: {equipment_traits}")
                
                hr_pos = html.find("<hr>", html.find("ctl00_RadDrawer1_Content_MainContent_DetailedOutput"))
                equipment_description = html[hr_pos + len("<hr>"):find_earliest_position(html.find("<hr>", hr_pos + 1), html.find("<h2", hr_pos + 1), html.find("</span>", hr_pos  + 1))]
                equipment_description = equipment_description.replace("<br>", "\n")
                equipment_description = remove_tags(equipment_description)
                
                while(equipment_description.lower().find("nethys note") > -1):
                    log("Found Nethys Note. Removing.")
                    note_pos = equipment_description.lower().find("nethys note")
                    note_end = equipment_description.lower().find(".", note_pos) + 1
                    equipment_description = equipment_description.replace(equipment_description[note_pos:note_end], "").strip()
                
                log(f"Description: {equipment_description}")

                price_start_pos = html.find("<b>Price</b>")
                price_end_pos = find_earliest_position(html.find(";", price_start_pos), html.find("\n", price_start_pos), html.find("<br>", price_start_pos), html.find("<hr>", price_start_pos))

                equipment_price = html[price_start_pos + len("<b>Price</b>"):price_end_pos].strip()
                
                log(f"Price: {equipment_price}")

                bulk_start_pos = html.find("<b>Bulk</b>")
                bulk_end_pos = find_earliest_position(html.find(";", bulk_start_pos), html.find("\n", bulk_start_pos), html.find("<br>", bulk_start_pos), html.find("<hr>", bulk_start_pos))

                equipment_bulk = html[bulk_start_pos + len("<b>Bulk</b>"):bulk_end_pos].strip()

                log(f"Bulk: {equipment_bulk}")

                equipment_category = url[:url.find(".")]
                
                log(f"Category: {equipment_category}")

                equipment_output.append([equipment_name, full_url, equipment_traits, equipment_category, equipment_level, equipment_price, equipment_bulk, equipment_description])

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
        log(f"Adding \"{equipment[0]}\",\"{equipment[1]}\",\"{equipment[2]}\",\"{equipment[3]}\",\"{equipment[4]}\",\"{equipment[5]}\",\"{equipment[6]}\", \"{equipment[7]}\" to Organzied Output")
        organized_output.append(f"\"{equipment[0]}\",\"{equipment[1]}\",\"{equipment[2]}\",\"{equipment[3]}\",\"{equipment[4]}\",\"{equipment[5]}\",\"{equipment[6]}\", \"{equipment[7]}\"")

    return organized_output
