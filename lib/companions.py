from os import remove
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

import lib.db
from lib.helper import remove_tags, find_earliest_position, find_which_exists
from lib.log import log_text as log

animal_companion_url = "https://2e.aonprd.com/AnimalCompanions.aspx"
undead_companion_url = "https://2e.aonprd.com/AnimalCompanions.aspx?Undead=true"

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
    
    log("Starting Undead Companion Upload Preperation")
    undead_companion_data = organize_animal_companion_data(undead_companion_url)
    log("Preparation Done")

    log("Starting INSERT Process")
    for companion in undead_companion_data:
        log("Inserting " + companion + " Into Database")
        conn = lib.db.query_database("INSERT INTO official_companions VALUES (" + companion + ");", connection=conn, close_conn=False)[0]

    log("Commiting Database Changes")
    conn.commit()
    log("Closing Connection")
    conn.close()

def grab_animal_companion_data(url=animal_companion_url):
    animal_companion_output = []

    log("Opening Browser")
    driver = webdriver.Chrome('./chromedriver.exe')
    log("Going to Page: " + url)
    driver.get(url)
    #log("Waiting for Page to Load")
    #time.sleep(5)

    log("Getting Page Source")
    html = driver.page_source
    log("Setting up BeautifulSoup with Source")
    soup = BeautifulSoup(html, "html.parser")

    log("Finding Detail Container")
    container = soup.find(id="ctl00_RadDrawer1_Content_MainContent_DetailedOutput")
    html = str(container)
    
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
        companion_name = companion.text.strip()
        log(f"Found {companion_name}")
        
        log("Getting Companion Link")
        links = companion.find_all("a")
        base_companion_link = ""
        
        for l in links:
            if l.get("href").startswith("AnimalCompanions.aspx"):
                base_companion_link = l.get("href")
                companion_link = "https://2e.aonprd.com/" + l.get("href")
                
        if html.find(f"href=\"{base_companion_link}\"") == -1:
            base_companion_link = base_companion_link.replace("&", "&amp;")       
                
        log(f"Found {companion_link}")
        link_pos = html.find(f"href=\"{base_companion_link}\"") + len(f"href=\"{base_companion_link}\"")
        
        log("Getting Companion Description")        
        description_start_pos = html.find("<br/>", link_pos) + len("<br/>")        
        description_end_pos = html.find("<br/>", description_start_pos)
        companion_description = html[description_start_pos:description_end_pos].strip()
        while companion_description.startswith("Your companion") == False and companion_description.startswith("Your animal companion") == False:
            description_start_pos = description_end_pos + len("<br/>")
            description_end_pos = html.find("<br/>", description_start_pos)
            companion_description = html[description_start_pos:description_end_pos].strip()        
        
        print(f"Start: {description_start_pos}, End: {description_end_pos}")
        companion_description = remove_tags(companion_description, "a")
        log(f"Found {companion_description}")
        
        log("Getting Companion Size")
        size_start_pos = html.find("<b>Size</b>", description_end_pos) + len("<b>Size</b>")
        size_end_pos = html.find("<br/>", size_start_pos)
        print(f"Start: {size_start_pos}, End: {size_end_pos}")
        companion_size = html[size_start_pos:size_end_pos].strip()
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
            damage_dice_end_pos = html.find("<br/>", damage_dice_start_pos)
            companion_attack_damage_dice = html[damage_dice_start_pos:damage_dice_end_pos].strip().split(" ")[0]
            companion_attack_damage_type = html[damage_dice_start_pos:damage_dice_end_pos].strip().split(" ")[1]
            companion_attacks.append([companion_attack_name.strip(), companion_attack_type.strip(), companion_attack_damage_dice.strip(), companion_attack_damage_type.strip()])
            log(f"Found {companion_attack_damage_dice}, {companion_attack_damage_type}")
            
            log("Checking For More Attacks")
            next_start_pos = html.find("<b>", damage_dice_end_pos) + len("<b>")
            next_end_pos = html.find("</b>", next_start_pos)
            next_category = html[next_start_pos:next_end_pos]
            log(f"The Next Category is {next_category}")
            
            if next_category != "Melee" and next_category != "Ranged":
                log("Found No More Attacks. Continuing")
                break
            else:
                log("Found Another Attack.")
                size_end_pos = damage_dice_end_pos
        
        log("Getting Stat Line String")
        stat_start_pos = damage_dice_end_pos + len("<br/>")
        stat_end_pos = html.find("<br/>", stat_start_pos)
        companion_stat_str = html[stat_start_pos:stat_end_pos]
        companion_stat_str = remove_tags(companion_stat_str, "b", True).strip()
        log(f"Found {companion_stat_str}")
        
        log("Getting Hit Points")
        hp_start_pos = html.find("</b>", stat_end_pos) + len("</b>")
        hp_end_pos = html.find("<br/>", hp_start_pos)
        companion_hit_points = html[hp_start_pos:hp_end_pos].strip()
        log(f"Found {companion_hit_points}")
        
        log("Getting Skill Training")
        senses_start_pos = html.find("<b>Senses</b>", hp_end_pos)
        if html.find("<u>", hp_end_pos) > -1:
            skill_list_start_pos = html.find("<u>", hp_end_pos) + len("<u>")
            skill_list_end_pos = html.find("</u>", skill_list_start_pos)
            while(skill_list_end_pos < senses_start_pos and skill_list_end_pos != -1):
                skill_list_text = html[skill_list_start_pos:skill_list_end_pos]
                skill_list_text = remove_tags(skill_list_text, "a")
                companion_skill_boost.append(skill_list_text)
                skill_list_start_pos = html.find("<u>", skill_list_end_pos + 1) + len("<u>")
                skill_list_end_pos = html.find("</u>", skill_list_start_pos)
                
            for c in companion_skill_boost:
                c = c.strip()
        else:
            companion_skill_boost.append("none (mindless)")
            skill_list_end_pos = html.find("<br/>", hp_end_pos + len("<br/>") + 1)
        log(f"Found {str(companion_skill_boost)}")
        
        log("Getting Senses")
        senses_start_pos = html.find("<b>Senses</b>", skill_list_end_pos) + len("<b>Senses</b>")
        senses_end_pos = html.find("<br/>", senses_start_pos)
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
                
        companion_senses = companion_senses[:-1].strip()
        
        log(f"Found {str(companion_senses)}")
        
        log("Getting Speed")
        speed_start_pos = html.find("<b>Speed</b>", senses_end_pos) + len("<b>Speed</b>")
        speed_end_pos = html.find("<br/>", speed_start_pos)
        companion_speed = html[speed_start_pos:speed_end_pos].strip()
        log(f"Found {companion_speed}")
        
        log("Getting Support Benefit")
        support_start_pos = html.find("<b>Support Benefit</b>", speed_end_pos) + len("<b>Support Benefit</b>")
        support_end_pos = html.find("<br/>", support_start_pos)
        companion_support_benefit = html[support_start_pos:support_end_pos]
        companion_support_benefit = remove_tags(companion_support_benefit, "a").strip()
        log(f"Found {companion_support_benefit}")
        
        log("Getting Advanced Maneuver")
        maneuver_start_pos = html.find("<b>Advanced Maneuver</b>", support_end_pos) + len("<b>Advanced Maneuver</b>")
        maneuver_end_pos = find_earliest_position(html.find("<br/>", maneuver_start_pos), html.find("<h3 ", maneuver_start_pos))
        companion_advanced_maneuver = html[maneuver_start_pos:maneuver_end_pos].strip()
        log(f"Found {companion_advanced_maneuver}")
        
        log("Getting Advanced Maneuver Summary")
        maneuver_summary_start_pos = html.find("<hr/>", maneuver_end_pos) + len("<hr/>")
        
        maneuver_summary_end_pos = find_earliest_position(
            html.find("<h2 ", maneuver_summary_start_pos), 
            html.find("<h3 ", maneuver_summary_start_pos),
            html.find("</span>", maneuver_summary_start_pos), 
            html.find("<br/>", maneuver_summary_start_pos), 
            html.find("<hr/> ", maneuver_summary_start_pos))
        
        companion_advanced_maneuver_summary = remove_tags(
            html[maneuver_summary_start_pos:maneuver_summary_end_pos], "a").strip()
        
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

    return animal_companion_output               
               
def grab_advanced_option_data():
    advanced_option_url = "https://2e.aonprd.com/AnimalCompanions.aspx?Advanced=true"
    
    advanced_option_output = []
    
    #Table Columns: Name, link, strength, dexterity, constitution, intelligence, wisdom, charisma, extra_wep_damage, skill_increases, attack_increases, defenses_increases, size_increases
            
    log("Opening Browser")
    driver = webdriver.Chrome('./chromedriver.exe')
    log("Going to Page: " + advanced_option_url)
    driver.get(advanced_option_url)
 
    log("Getting Page Source")
    html = driver.page_source
    log("Setting up BeautifulSoup with Source")
    soup = BeautifulSoup(html, "html.parser")

    log("Finding Detail Container")
    container = soup.find(id="ctl00_RadDrawer1_Content_MainContent_DetailedOutput")
    html = str(container)
    
    log("Getting All Advanced Options Headings")
    heading_list = container.find_all("h2")
    
    log("Searching All Options For Companion Changes")
    for heading in heading_list:
        option_description = ""
        
        stat_list = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
        skill_list = ["Athletics", "Acrobatics", "Perception", "Arcana", "Crafting", "Deception", "Diplomacy", "Intimidation", "Medicine", "Nature", "Occultism", "Performance", "Religion", "Society", "Stealth", "Survival", "Thievery", "Lore"]
        
        option_name = ""
        option_link = ""
        strength_increase = ""
        dexterity_increase = ""
        constitution_increase = ""
        intelligence_increase = ""
        wisdom_increase = ""
        charisma_increase = ""
        extra_wep_damage = ""
        skill_increases = ""
        defenses_increases = ""
        attack_increases = ""
        size_increases = ""
        magical_attacks = ""
        
        log("Getting Name and Link")
        option_name = heading.text
        links = heading.find_all("a")
        for l in links:
            if l.get("href").startswith("AnimalCompanions.aspx"):
                option_link = "https://2e.aonprd.com/" + l.get("href")
        log(f"Found: {option_name}, {option_link}")
        
        heading_pos = html.find(f"{option_name}</a></h2>")
        
        log("Getting Full Description")
        description_start_pos = html.find("<br>", html.find("<b>Source</b>", heading_pos)) + len("<br>")
        if description_start_pos == len("<br>") - 1:
            description_start_pos = html.find("<br/>", html.find("<b>Source</b>", heading_pos)) + len("<br/>")
        description_end_pos = html.find("<br><h2 ", description_start_pos)
        if description_end_pos == -1:
            description_end_pos = html.find("<br/><h2 ", description_start_pos)
        
        option_description = html[description_start_pos:description_end_pos]
        option_description = option_description.replace("<br>", "")
        option_description = option_description.replace("<br/>", "")
        option_description = option_description.replace("<hr>", "")
        option_description = option_description.replace("<hr/>", "")
        option_description = remove_tags(option_description)
        log(f"Found: {option_description}")
        
        description_sentences = option_description.split(".")
                
        log("Looking For Stat Increases")
        for sentence in description_sentences:
            for stat in stat_list:
                if stat in sentence:
                    log(f"Found {stat} in {sentence}")
                    sentence_words = sentence.split(" ")
                    after_stat = False
                    for word in sentence_words:
                        word = word.replace(".", "")
                        word = word.replace(",", "")
                        if word == stat:
                            after_stat = True
                        if word.isnumeric() and after_stat == True:
                            if stat == "Strength":
                                strength_increase = int(word)
                                after_stat = False
                                log(f"Strength Increases By {strength_increase}")
                                break
                            if stat == "Dexterity":
                                dexterity_increase = int(word)
                                after_stat = False
                                log(f"Dexterity Increases By {dexterity_increase}")
                                break
                            if stat == "Constitution":
                                constitution_increase = int(word)
                                after_stat = False
                                log(f"Constitution Increases By {constitution_increase}")
                                break
                            if stat == "Intelligence":
                                intelligence_increase = int(word)
                                after_stat = False
                                log(f"Intelligence Increases By {intelligence_increase}")
                                break
                            if stat == "Wisdom":
                                wisdom_increase = int(word)
                                after_stat = False
                                log(f"Wisdom Increases By {wisdom_increase}")
                                break
                            if stat == "Charisma":
                                charisma_increase = int(word)
                                after_stat = False
                                log(f"Charisma Increases By {charisma_increase}")
                                break
                            
        log("Finding Extra Weapon Damage")
        for sentence in description_sentences:
            if "additional damage with its unarmed attacks" in sentence:
                log("Found Additional Damage. Looking For Value")
                word_list = sentence.split(" ")
                for word in word_list:
                    if word.isnumeric():
                        extra_wep_damage = int(word)
                        log(f"Found: {extra_wep_damage}")
                            
        log("Finding Skill Increases")
        for skill in skill_list:
            if skill in option_description:
                log(f"Found: {skill}")
                skill_increases += f"{skill},"
                
        if skill_increases != "":
            skill_increases = skill_increases[:-1]
            
        log(f"Skill Increases: {skill_increases}")
        
        log("Finding Attack Increases")
        for sentence in description_sentences:
            if "proficiency" in sentence and ("unarmed attacks" in sentence or "unarmed strikes" in sentence):
                attack_increases = "One Step"
                break
                
        log("Finding If Attacks Are Magical")
        for sentence in description_sentences:
            if "attacks count as magical" in sentence or "attacks become magical" in sentence or "strikes count as magical" in sentence or "strikes become magical" in sentence:
                magical_attacks = "Yes"
                break

        log("Finding Defense Increases")
        for sentence in description_sentences:
            if "gain resistance" in sentence:
                log("Found Resistances")
                word_list = sentence.split(" ")
                for word in word_list:
                    if word.isnumeric():
                        value = int(word)
                        defenses_increases += f"resistance {value} (see page for details),"
            if "barding" in sentence:
                log("Found Barding")
                defenses_increases += "barding,"
            if "unarmored" in sentence:
                log("Found Unarmored")
                defenses_increases += "unarmored,"
        
        defenses_increases = defenses_increases[:-1]
        
        log(f"Defence Increases: {defenses_increases}")        
            
        log("Finding Size Increases")
        if "grows in size" in option_description or "grows by one size" in option_description:
            log(f"Found Size Increase")
            size_increases = "One Size"
                
        advanced_option_output.append([option_name, option_link, strength_increase, dexterity_increase, constitution_increase, intelligence_increase, wisdom_increase, charisma_increase, attack_increases, magical_attacks, extra_wep_damage, defenses_increases, skill_increases, size_increases])                  
                    
    log(advanced_option_output)    
 
def organize_animal_companion_data(url=animal_companion_url):
    log("Getting Animal Companion Data")
    animal_companion_output = grab_animal_companion_data(url)
    organized_output = []
    log("Starting to Organize Data")

    for ac in animal_companion_output:
        log(f"Adding {ac} to Organized Output String")
        attack_name_str = ""
        attack_type_str = ""
        attack_damage_dice_str = ""
        attack_damage_type_str = ""
        skill_str = ""
        
        stat_list = ac[5].split(" ")
        
        strength_str = stat_list[0][:-1]
        dexterity_str = stat_list[2][:-1]
        constitution_str = stat_list[4][:-1]
        intelligence_str = stat_list[6][:-1]
        wisdom_str = stat_list[8][:-1]
        charisma_str = stat_list[10]
        
        for attack in ac[4]:
            attack_name_str += attack[0].strip()
            attack_type_str += attack[1].strip() + ","
            attack_damage_dice_str += attack[2].strip() + ","
            attack_damage_type_str += attack[3].strip() + ","
            
        attack_name_str = attack_name_str[:-1]
        attack_type_str = attack_type_str[:-1]
        attack_damage_dice_str = attack_damage_dice_str[:-1]
        attack_damage_type_str = attack_damage_type_str[:-1]
            
        for skill in ac[7]:
            skill_str += skill + ","
        
        skill_str = skill_str[:-1]
            
        organized_output.append(f"\"{ac[0]}\", \"{ac[1]}\", \"{ac[2]}\", \"{ac[3]}\", \"{attack_name_str}\", \"{attack_type_str}\", \"{attack_damage_dice_str}\", \"{attack_damage_type_str}\", \"{strength_str}\",\"{dexterity_str}\",\"{constitution_str}\", \"{intelligence_str}\",\"{wisdom_str}\",\"{charisma_str}\", {ac[6]}, \"{skill_str}\", \"{ac[8]}\", \"{ac[9]}\", \"{ac[10]}\", \"{ac[11]}\", \"{ac[12]}\"")
        log(f"Added \"{ac[0]}\", \"{ac[1]}\", \"{ac[2]}\", \"{ac[3]}\", \"{attack_name_str}\", \"{attack_type_str}\", \"{attack_damage_dice_str}\", \"{attack_damage_type_str}\", \"{strength_str}\",\"{dexterity_str}\",\"{constitution_str}\", \"{intelligence_str}\",\"{wisdom_str}\",\"{charisma_str}\", {ac[6]}, \"{skill_str}\", \"{ac[8]}\", \"{ac[9]}\", \"{ac[10]}\", \"{ac[11]}\", \"{ac[12]}\" to Organized Output")

    return organized_output
