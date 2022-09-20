from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

import lib.db
from lib.helper import remove_tags, find_earliest_position, find_which_exists
from lib.log import log_text as log

animal_companion_url = "https://2e.aonprd.com/AnimalCompanions.aspx"

def upload_companion_data():
    log("Starting Animal Companion Upload Preperation")
    animal_companion_data = organize_animal_companion_data()
    log("Preparation Done")

    log("Clearing Table")
    conn, row_count, result = lib.db.query_database("DELETE FROM official_companions;", get_result=True, close_conn=False)

    log("Starting INSERT Process")
    for companion in animal_companion_data:
        log("Inserting " + companion + " Into Database")
        conn = lib.db.query_database("INSERT INTO official_companions VALUES (" + companion + ");", connection=conn, close_conn=False)[0]

    log("Commiting Database Changes")
    conn.commit()
    log("Closing Connection")
    conn.close()

def grab_animal_companion_data():
    animal_companion_output = []

    log("Opening Browser")
    driver = webdriver.Chrome('./chromedriver.exe')
    log("Going to Page: " + animal_companion_url)
    driver.get(animal_companion_url)
    #log("Waiting for Page to Load")
    #time.sleep(5)

    log("Getting Page Source")
    html = driver.page_source
    log("Setting up BeautifulSoup with Source")
    soup = BeautifulSoup(html, "html.parser")

    log("Finding Detail Container")
    container = soup.find(id="ctl00_RadDrawer1_Content_MainContent_DetailedOutput")
    container_pos = html.find("ctl00_RadDrawer1_Content_MainContent_DetailedOutput")
    log("Finding All Animal Headings in Container")
    companion_header_list = container.find_all("h2")
    
    log("Searching Through Companions for Data")
    for companion in companion_header_list:
        heading_pos = html.find(str(companion), container_pos)
        
        companion_name = ""
        companion_link = ""
        companion_description = ""
        companion_size = ""
        companion_attack_type = ""
        companion_attack_name = ""
        companion_attack_damage_dice = ""
        companion_attack_damage_type = ""
        companion_attacks = []
        companion_stat_str = ""
        companion_hit_points = ""
        companion_skill_boost = ""
        companion_senses = ""
        companion_speed = ""
        companion_support_benefit = ""
        companion_advanced_maneuver = ""
        companion_advanced_maneuver_summary = ""
        
        log("Getting Companion Name")
        companion_name = companion.text
        log(f"Found {companion_name}")
        
        log("Getting Companion Link")
        links = companion.find_all("a")
        
        for l in links:
            if l.get("href").startswith("AnimalCompanions.aspx"):
                companion_link = "https://2e.aonprd.com/" + l.get("href")
                
        log(f"Found {companion_link}")
        
        log("Getting Companion Description")
        description_start_pos = html.find("<br>", heading_pos) + len("<br>")
        description_end_pos = html.find("<br>", description_start_pos)
        companion_description = html[description_start_pos:description_end_pos]
        log(f"Found {companion_description}")
        
        log("Getting Companion Size")
        size_start_pos = html.find("<b>Size</b>", description_end_pos) + len("<b>Size</b>")
        size_end_pos = html.find("<br>", size_start_pos)
        companion_size = html[size_start_pos:size_end_pos]
        log(f"Found {companion_size}")
        
        log("Getting Attack Type")
        attack_type_start_pos = html.find("<b>", size_end_pos) + len("<b>")
        attack_type_end_pos = html.find("</b>", attack_type_start_pos)
        companion_attack_type = html[attack_type_start_pos:attack_type_end_pos]
        log(f"Found {companion_attack_type}")
        
        log("Getting Attack Name")
        attack_name_start_pos = html.find("</span>", attack_type_end_pos) + len("</span>")
        attack_name_end_pos = html.find("<b>", attack_name_start_pos)
        companion_attack_name = html[attack_name_start_pos:attack_name_end_pos]
        log(f"Found {companion_attack_name}")
        
        
        
def organize_animal_companion_data():
    pass