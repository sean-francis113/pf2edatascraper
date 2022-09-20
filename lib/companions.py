from os import remove
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
        companion_skill_boost = []
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
        base_companion_link = ""
        
        for l in links:
            if l.get("href").startswith("AnimalCompanions.aspx"):
                base_companion_link = l.get("href")
                companion_link = "https://2e.aonprd.com/" + l.get("href")
                
        log(f"Found {companion_link}")
        link_pos = html.find(f"<a href=\"{base_companion_link}\">") + len(f"<a href=\"{base_companion_link}\">")
        
        log("Getting Companion Description")
        description_start_pos = html.find("<br>", link_pos) + len("<br>")
        description_end_pos = html.find("<br>", description_start_pos)
        companion_description = html[description_start_pos:description_end_pos]
        log(f"Found {companion_description}")
        
        log("Getting Companion Size")
        size_start_pos = html.find("<b>Size</b>", description_end_pos) + len("<b>Size</b>")
        size_end_pos = html.find("<br>", size_start_pos)
        companion_size = html[size_start_pos:size_end_pos]
        log(f"Found {companion_size}")
        
        while(True):
            log("Getting Attack Type")
            attack_type_start_pos = html.find("<b>", size_end_pos) + len("<b>")
            attack_type_end_pos = html.find("</b>", attack_type_start_pos)
            companion_attack_type = html[attack_type_start_pos:attack_type_end_pos]
            log(f"Found {companion_attack_type}")
            
            log("Getting Attack Name")
            attack_name_start_pos = html.find("</span>", attack_type_end_pos) + len("</span>")
            attack_name_end_pos = html.find("<b>", attack_name_start_pos)
            companion_attack_name = html[attack_name_start_pos:attack_name_end_pos]
            companion_attack_name = remove_tags(companion_attack_name)
            log(f"Found {companion_attack_name}")
            
            log("Getting Damage Dice and Type")
            damage_dice_start_pos = html.find("</b>", attack_name_end_pos) + len("</b>")
            damage_dice_end_pos = html.find("<br>", damage_dice_start_pos)
            companion_attack_damage_dice = html[damage_dice_start_pos:damage_dice_end_pos].split(" ")[0]
            companion_attack_damage_type = html[damage_dice_start_pos:damage_dice_end_pos].split(" ")[1]
            companion_attacks.append([companion_attack_name, companion_attack_type, companion_attack_damage_dice, companion_attack_type])
            log(f"Found {companion_attack_damage_dice}, {companion_attack_damage_type}")
            
            log("Checking For More Attacks")
            next_start_pos = html.find("<b>", damage_dice_end_pos) + len("<b>")
            next_end_pos = html.find("</b>", next_start_pos)
            next_category = html[next_start_pos:next_end_pos]
            log(f"The Next Category is {next_category}")
            
            if next_category.find("Melee") == -1 or next_category.find("Ranged") == -1:
                log("Found No More Attacks. Continuing")
                break
            else:
                log("Found Another Attack.")
        
        log("Getting Stat Line String")
        stat_start_pos = damage_dice_end_pos + len("<br>")
        stat_end_pos = html.find("<br>", stat_start_pos)
        companion_stat_str = html[stat_start_pos:stat_end_pos]
        companion_stat_str = remove_tags(companion_stat_str, "b", True)
        log(f"Found {companion_stat_str}")
        
        log("Getting Hit Points")
        hp_start_pos = html.find("</b>", stat_end_pos) + len("</b>")
        hp_end_pos = html.find("<br>", hp_start_pos)
        companion_hit_points = html[hp_start_pos:hp_end_pos]
        log(f"Found {companion_hit_points}")
        
        log("Getting Skill Training")
        skill_list_start_pos = html.find("<u>", hp_end_pos) + len("<u>")
        skill_list_end_pos = html.find("</u>", skill_list_start_pos)
        skill_list_text = html[skill_list_start_pos:skill_list_end_pos]
        skill_list_text = remove_tags(skill_list_text, "a")
        companion_skill_boost = skill_list_text.split(",")
        log(f"Found {str(companion_skill_boost)}")
        
        log("Getting Senses")
        senses_start_pos = html.find("<b>Senses</b>", skill_list_end_pos) + len("<b>Senses</b>")
        senses_end_pos = html.find("<br>", senses_start_pos)
        senses_text = html[senses_start_pos:senses_end_pos]
        senses_text = remove_tags(senses_text, "a")
        senses_list = senses_text.split(",")
        temp_str = ""
        found_parenthesis = False
        for sense in senses_list:
            if "(" in sense:
                temp_str += sense
            elif ")" in sense:
                temp_str += sense
                companion_senses += temp_str + ", "
                temp_str = ""
            else:
                companion_senses += sense + ", "
        
        log(f"Found {str(companion_senses)}")
        
        log("Getting Speed")
        speed_start_pos = html.find("<b>Speed</b>", senses_end_pos) + len("<b>Speed</b>")
        speed_end_pos = html.find("<br>", speed_start_pos)
        companion_speed = html[speed_start_pos:speed_end_pos]
        log(f"Found {companion_speed}")
        
        log("Getting Support Benefit")
        support_start_pos = html.find("<b>Support Benefit</b>", speed_end_pos) + len("<b>Support Benefit</b>")
        support_end_pos = html.find("<br>", support_start_pos)
        companion_support_benefit = html[support_start_pos:support_end_pos]
        companion_support_benefit = remove_tags(companion_support_benefit, "a")
        log(f"Found {companion_support_benefit}")
        
        log("Getting Advanced Maneuver")
        maneuver_start_pos = html.find("<b>Advanced Maneuver</b>", support_end_pos) + len("<b>Advanced Maneuver</b>")
        maneuver_end_pos = find_earliest_position(html.find("<br>", maneuver_start_pos), html.find("<h3 ", maneuver_start_pos))
        companion_advanced_maneuver = html[maneuver_start_pos:maneuver_end_pos]
        log(f"Found {companion_advanced_maneuver}")
        
        log("Getting Advanced Maneuver Summary")
        maneuver_summary_start_pos = html.find("<hr>", maneuver_end_pos) + len("<hr>")
        
        maneuver_summary_end_pos = find_earliest_position(
            html.find("<h2 ", maneuver_summary_start_pos), 
            html.find("<h3 ", maneuver_summary_start_pos),
            html.find("</span>", maneuver_summary_start_pos), 
            html.find("<br>", maneuver_summary_start_pos), 
            html.find("<hr> ", maneuver_summary_start_pos))
        
        companion_advanced_maneuver_summary = remove_tags(
            html[maneuver_summary_start_pos:maneuver_summary_end_pos], "a")
        
        log(f"Found {companion_advanced_maneuver_summary}")
        
        log(str([companion_name, companion_link, companion_description, 
                companion_size, companion_attacks, companion_stat_str, 
                companion_hit_points, companion_skill_boost, 
                companion_senses, companion_speed, companion_support_benefit, 
                companion_advanced_maneuver, 
                companion_advanced_maneuver_summary]))
        
        animal_companion_output.append([companion_name, companion_link, companion_description, 
                                        companion_size, companion_attacks, companion_stat_str, 
                                        companion_hit_points, companion_skill_boost, 
                                        companion_senses, companion_speed, companion_support_benefit, 
                                        companion_advanced_maneuver, 
                                        companion_advanced_maneuver_summary])               
                
def organize_animal_companion_data():
    pass