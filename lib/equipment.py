from os import remove
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time

import lib.db
from lib.helper import remove_tags, find_earliest_position, find_which_exists
from lib.log import log_text as log

url = "https://2e.aonprd.com/Equipment.aspx?All=true"
test_limit = 0

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
    equipment_output = []

    log("Opening Browser")
    driver = webdriver.Chrome('./chromedriver.exe')
    log("Going to Page: " + url)
    driver.get(url)
    #log("Waiting for Page to Load")
    #time.sleep(5)
    
    log("Setting Table to Show All Rows")
    input_box = driver.find_element(By.ID, "ctl00_RadDrawer1_Content_MainContent_Rad_AllEquipment_ctl00_ctl03_ctl02_ChangePageSizeTextBox")
    input_box.send_keys("1000000")
    input_box.send_keys(Keys.ENTER)
    
    log("Getting Page Source")
    html = driver.page_source
    log("Setting up BeautifulSoup with Source")
    soup = BeautifulSoup(html, "html.parser")

    log("Finding Table")
    container = soup.find("table", id="ctl00_RadDrawer1_Content_MainContent_Rad_AllEquipment_ctl00")
    
    log("Getting Table Body")
    table_body = container.find("tbody")
    
    log("Getting Table Rows")
    table_rows = table_body.find_all("tr")
    
    ignore_col = [2, 3, 4, 6, 10]
    
    i = 1
    get_link = True
    x = 1
    
    log("Looking Through Rows for Data")
    for row in table_rows:
        row_data = row.find_all("td")
        data_output = []
        for data in row_data:
            if i in ignore_col:
                log(f"Ignoring Column {i}")
                i += 1
                continue
            
            data_text = data.text.replace("\n", "")
            log(f"Found: {data_text}")
            data_output.append(data_text)
            
            if get_link:
                links = data.find_all("a")
                for l in links:
                    if l.get("href").startswith("Equipment.aspx") or l.get("href").startswith("Vehicles.aspx") or l.get("href").startswith("Weapons.aspx") or l.get("href").startswith("Armor.aspx") or l.get("href").startswith("Shields.aspx"):
                        data_output.append("https://2e.aonprd.com/" + l.get("href"))
                        get_link = False
            
            i += 1
        
        log(f"Data Output: {data_output}")    
        equipment_output.append(data_output)
        i = 1
        get_link = True
        
        if test_limit > 0 and x == test_limit:
            break
        
        x += 1
            
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
