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
stat_list = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
skill_list = ["Athletics", "Acrobatics", "Perception", "Arcana", "Crafting", "Deception", "Diplomacy", "Intimidation", "Medicine", "Nature", "Occultism", "Performance", "Religion", "Society", "Stealth", "Survival", "Thievery", "Lore"]
size_list = ["Small", "Medium", "Large"]
proficiency_list = ["Untrained", "Trained", "Expert", "Master", "Legendary"]
saving_throw_list = ["Fortitude", "Reflex", "Will"]
weapon_trait_list = ["Agile", "Finesse"]

def upload_companion_data():
    log("Starting Animal Companion Upload Preperation")
    animal_companion_data = organize_animal_companion_data()
    advanced_option_data = organize_advanced_data()
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

    log("Clearing Table")
    conn = lib.db.query_database("DELETE FROM official_companion_options;", connection=conn, close_conn=False)[0]

    log("Starting INSERT Process")
    for option in advanced_option_data:
        log("Inserting " + option + " Into Database")
        conn = lib.db.query_database("INSERT INTO official_companion_options VALUES (" + option + ");", connection=conn, close_conn=False)[0]

    log("Starting Construct Companion Upload Preperation")
    construct_companion_data = organize_construct_companion_data()
    log("Preparation Done")
    
    log("Clearing Table")
    conn, row_count, result = lib.db.query_database("DELETE FROM official_construct_companions;", get_result=True, close_conn=False)

    log("Starting INSERT Process")
    for construct in construct_companion_data:
        log("Inserting " + construct + " Into Database")
        conn = lib.db.query_database("INSERT INTO official_construct_companions VALUES (" + construct + ");", connection=conn, close_conn=False)[0]

    log("Commiting Database Changes")
    conn.commit()
    log("Closing Connection")
    conn.close()

def grab_animal_companion_data(url=animal_companion_url):
    global skill_list
    global stat_list
    
    animal_companion_output = []

    log("Opening Browser")
    driver = webdriver.Chrome('./chromedriver.exe')
    log("Going to Page: " + url)
    driver.get(url)
    log("Waiting for Page to Load")
    time.sleep(5)

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
        
        companion_description = remove_tags(companion_description, "a")
        log(f"Found {companion_description}")
        
        log("Getting Companion Size")
        size_start_pos = html.find("<b>Size</b>", description_end_pos) + len("<b>Size</b>")
        size_end_pos = html.find("<br/>", size_start_pos)
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
        skill_start_pos = html.find("<b>Skill</b>", hp_end_pos) + len("<b>Skill</b>")
        if skill_start_pos == len("<b>Skill</b>") - 1:
            skill_start_pos = html.find("<b>Skills</b>", hp_end_pos) + len("<b>Skills</b>")
        skill_end_pos = html.find("<br>", skill_start_pos)
        if skill_end_pos == -1:
            skill_end_pos = html.find("<br/>", skill_start_pos)
            
        companion_skill_boost = remove_tags(html[skill_start_pos:skill_end_pos]).split(",")
        log(f"Found {str(companion_skill_boost)}")
        
        log("Getting Senses")
        senses_start_pos = html.find("<b>Senses</b>", skill_end_pos) + len("<b>Senses</b>")
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
    specialization_option_url = "https://2e.aonprd.com/AnimalCompanions.aspx?Specialized=true"
    url_list = [advanced_option_url,specialization_option_url]
    
    advanced_option_output = []
    
    for url in url_list:        
        log("Opening Browser")
        driver = webdriver.Chrome('./chromedriver.exe')
        log("Going to Page: " + url)
        driver.get(url)
    
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
            option_type = ""
            if url == advanced_option_url:
                option_type = "Advanced"
            else:
                option_type = "Specialization"
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
                                    strength_increase = word
                                    after_stat = False
                                    log(f"Strength Increases By {strength_increase}")
                                    break
                                if stat == "Dexterity":
                                    dexterity_increase = word
                                    after_stat = False
                                    log(f"Dexterity Increases By {dexterity_increase}")
                                    break
                                if stat == "Constitution":
                                    constitution_increase = word
                                    after_stat = False
                                    log(f"Constitution Increases By {constitution_increase}")
                                    break
                                if stat == "Intelligence":
                                    intelligence_increase = word
                                    after_stat = False
                                    log(f"Intelligence Increases By {intelligence_increase}")
                                    break
                                if stat == "Wisdom":
                                    wisdom_increase = word
                                    after_stat = False
                                    log(f"Wisdom Increases By {wisdom_increase}")
                                    break
                                if stat == "Charisma":
                                    charisma_increase = word
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
                            extra_wep_damage = word
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
                if "resistance" in sentence and "resistance" not in defenses_increases:
                    log("Found Resistances")
                    word_list = sentence.split(" ")
                    for word in word_list:
                        if word.isnumeric():
                            value = word
                            defenses_increases += f"resistance {value} (see page for details),"
                if "barding" in sentence and "barding" not in defenses_increases:
                    log("Found Barding")
                    defenses_increases += "barding,"
                if "unarmored" in sentence and "unarmored" not in defenses_increases:
                    log("Found Unarmored")
                    defenses_increases += "unarmored,"
            
            defenses_increases = defenses_increases[:-1]
            
            log(f"Defence Increases: {defenses_increases}")        
                
            log("Finding Size Increases")
            if "grows in size" in option_description or "grows by one size" in option_description:
                log(f"Found Size Increase")
                size_increases = "One Size"
                    
            advanced_option_output.append([option_name, option_link, option_type, strength_increase, dexterity_increase, constitution_increase, intelligence_increase, wisdom_increase, charisma_increase, attack_increases, magical_attacks, extra_wep_damage, defenses_increases, skill_increases, size_increases])                  
                    
    log(advanced_option_output)
    return advanced_option_output

def grab_construct_companion_data():
    global stat_list
    global size_list
    global skill_list
    global proficiency_list
    global saving_throw_list
    
    construct_companion_url = "https://2e.aonprd.com/Rules.aspx?ID=1600"
    construct_output = []
    
    log("Opening Browser")
    driver = webdriver.Chrome('./chromedriver.exe')
    log("Going to Page: " + construct_companion_url)
    driver.get(construct_companion_url)

    log("Getting Page Source")
    html = driver.page_source
    log("Setting up BeautifulSoup with Source")
    soup = BeautifulSoup(html, "html.parser")

    log("Finding Detail Container")
    container = soup.find(id="ctl00_RadDrawer1_Content_MainContent_DetailedOutput")
    html = str(container)
    
    log("Getting All Construct Category Headings")
    heading_list = container.find_all("h1")
    
    for heading in heading_list:
        construct_type_name = ""
        construct_link = ""
        construct_traits = "Construct"
        construct_size = ""
        construct_senses = ""
        construct_speed = ""
        construct_hp = ""
        construct_stat_line = ""
        construct_attack_proficiency = ""
        construct_defense_proficiency = ""
        construct_skill_proficiency = ""
        construct_saving_throws_proficiency = ""
        construct_attacks = ""
        construct_extra_damage = ""
        construct_immunities = ""
        
        heading_text = heading.text
        
        if heading_text.startswith("Riding") or heading_text.startswith("Construct"):
            log(f"Ignoring {heading_text}")
            continue
        
        construct_type_name = heading_text.split(" ")[0]
        links = heading.find_all("a")
        for l in links:
            if l.get("href").startswith("Rules.aspx"):
                construct_link = "https://2e.aonprd.com/" + l.get("href")
                
        heading_pos = html.find(f"{heading.text}</a>")
        
        log(f"Category Name is {construct_type_name}")
        description_start_pos = html.find("<br>", heading_pos) + len("<br>")
        if description_start_pos == len("<br>") - 1:
            description_start_pos = html.find("<br/>", heading_pos) + len("<br/>")
            
        description_end_pos = html.find("<h1 ", description_start_pos)
        
        log(f"Formatting Description to Search Through")
        description = html[description_start_pos:description_end_pos]
        description = remove_tags(description, "h2", True)
        description = description.replace("<b>Source</b>", "")
        description = description.replace("Guns & Gears pg. 33", "")
        description = description.replace("<br>", "")
        description = description.replace("<br/>", "")
        description = remove_tags(description)
        
        description_sentences = description.split(".")
        
        log("Searching Through Description Sentence by Sentence")
        for sentence in description_sentences:
            sentence = sentence.strip()
            log(f"Searching: {sentence}")
            if "Small" in sentence or "Medium" in sentence or "Large" in sentence:
                log("Found Sizes")
                for size in size_list:
                    if size in sentence:
                        construct_size += size + ","
                construct_size = construct_size[:-1]
                log(f"Found {construct_size}")
            
            if "unarmed attacks" in sentence or "unarmed strikes" in sentence:
                log("Found Unarmed Attacks")
                for proficiency in proficiency_list:
                    if proficiency in sentence or proficiency.lower() in sentence:
                        construct_attack_proficiency = proficiency
                        log(f"Found {construct_attack_proficiency}")
                        break
                    
            if "first unarmed attack" in sentence.lower() or "other unarmed attack" in sentence.lower():
                log("Found an Attack")
                damage = ""
                damage_type = ""
                damage_traits = ""
                
                for word in sentence.split(" "):
                    if word.find("1d") > -1:
                        damage = word
                    elif word.find("bludgeoning") > -1 or word.find("piercing") > -1 or word.find("slashing") > -1:
                        damage_type = word.capitalize()
                    elif word.find("traits") > -1:
                        for trait in weapon_trait_list:
                            if trait.lower() in sentence.lower():
                                damage_traits += f"{trait},"
                
                damage_traits = damage_traits[:-1]
                construct_attacks += f"{damage}{damage_type}({damage_traits});"
                log(f"Found: {construct_attacks}")    
                    
            if "unarmored" in sentence or "unarmored" in sentence:
                log("Found Unarmored Defense")
                for proficiency in proficiency_list:
                    if proficiency in sentence or proficiency.lower() in sentence:
                        construct_defense_proficiency = proficiency
                        log(f"Found {construct_defense_proficiency}")
                        break
                    
            if "all saving throws" in sentence.lower():
                log("Found All Saving Throws")
                for proficiency in proficiency_list:
                    if proficiency in sentence or proficiency.lower() in sentence:
                        construct_saving_throws_proficiency = proficiency
                        log(f"Found All Saving Throws: {construct_saving_throws_proficiency}")
                        break
            elif "fortitude" in sentence.lower() or "reflex" in sentence.lower() or "will" in sentence.lower():
                for save in saving_throw_list:
                    if save in sentence or save.lower() in sentence:
                        log(f"Found {save}")
                        for proficiency in proficiency_list:
                            if proficiency in sentence or proficiency.lower() in sentence:
                                construct_saving_throws_proficiency += f"{save}:{proficiency},"
                                log(f"Found {save}: {proficiency}")
                                break
                construct_saving_throws_proficiency = construct_saving_throws_proficiency[:-1]
            elif "saving throws" in sentence.lower():
                log("Found All Saving Throws")
                for proficiency in proficiency_list:
                    if proficiency in sentence or proficiency.lower() in sentence:
                        construct_saving_throws_proficiency = proficiency
                        log(f"Found All Saving Throws: {construct_saving_throws_proficiency}")
                        break
                
            for skill in skill_list:
                if skill.lower() in sentence.lower():
                    log(f"Found {skill}")
                    for proficiency in proficiency_list:
                        if proficiency.lower() in sentence.lower():
                            construct_skill_proficiency += f"{skill}:{proficiency},"
                            log(f"Found {skill}: {proficiency}")
                            break
            if construct_skill_proficiency != "" and construct_skill_proficiency[-1] == ",":
                construct_skill_proficiency = construct_skill_proficiency[:-1]
                            
            if "base ability modifiers" in sentence.lower():
                log("Finding Stat Line")
                construct_stat_line = sentence[sentence.find("Str"):sentence.find("Cha") + len("Cha") + 3]
                construct_stat_line = construct_stat_line.replace("Str ", "")
                construct_stat_line = construct_stat_line.replace("Dex ", "")
                construct_stat_line = construct_stat_line.replace("Con ", "")
                construct_stat_line = construct_stat_line.replace("Int ", "")
                construct_stat_line = construct_stat_line.replace("Wis ", "")
                construct_stat_line = construct_stat_line.replace("Cha ", "")
                log(f"Found: {construct_stat_line}")
                
            if "hit points" in sentence.lower() and construct_hp == "":
                log(f"Found Hit Points")
                find_extra_hp = False
                base_hp = ""
                extra_hp = ""
                for word in sentence.split(" "):
                    if word.isnumeric():
                        if find_extra_hp == False:
                            base_hp = word
                            find_extra_hp = True
                        else:
                            extra_hp = word
                            break
                construct_hp = f"{base_hp}/{extra_hp}"
                log(f"Found: {construct_hp}")
                
            if "immune" in sentence.lower():
                log(f"Found Immunities")
                construct_immunities = "Immune: " + sentence[sentence.lower().find("immune to") + len("immune to"):]
                log(f"Found: {construct_immunities}")
            
            if "speed of" in sentence.lower() and "feet" in sentence.lower():
                log(f"Found Speed")
                for word in sentence.split(" "):
                    if word.isnumeric():
                        construct_speed = f"{word} feet"
                        break
                log(f"Found: {construct_speed}")
                
            if "precise" in sentence.lower() or "imprecise" in sentence.lower() or "vague" in sentence.lower() or "no sense" in sentence.lower():
                log(f"Found Senses")
                construct_senses = sentence[find_earliest_position(sentence.find("precise"), sentence.find("imprecise"), sentence.find("vague"), sentence.find("no sense")):]
                log(f"Found: {construct_senses}")
                
            if "modifiers by" in sentence and "Increase" in sentence:
                log("Found Modifier Increases")
                strength_increase = ""
                dexterity_increase = ""
                constitution_increase = ""
                intelligence_increase = ""
                wisdom_increase = ""
                charisma_increase = ""
                increase_by = ""
                
                words = sentence.split(" ")
                increase_by = words[-1]
                
                if "Strength" in sentence:
                    strength_increase = increase_by
                if "Dexterity" in sentence:
                    dexterity_increase = increase_by
                if "Constitution" in sentence:
                    constitution_increase = increase_by
                if "Intelligence" in sentence:
                    intelligence_increase = increase_by
                if "Wisdom" in sentence:
                    wisdom_increase = increase_by
                if "Charisma" in sentence:
                    charisma_increase = increase_by
                            
                construct_stat_line = f"{strength_increase},{dexterity_increase},{constitution_increase},{intelligence_increase},{wisdom_increase},{charisma_increase}"
                log(f"Found: {construct_stat_line}")            

            if "attack damage from" in sentence.lower() and "Increase" in sentence:
                if "two dice" in sentence:
                    log("Found Extra Dice of Damage")
                    construct_extra_damage = "Extra Dice"
                
            if "additional damage" in sentence:
                log("Found Extra Damage")
                for word in sentence.split(" "):
                    if word.isnumeric():
                        construct_extra_damage = word
                        log(f"Found: {construct_extra_damage}")
                
                if "magical" in sentence.lower():
                    construct_extra_damage += "(Magical)"
                    log("Found Magical Attacks")
        
        construct_output.append([construct_type_name, construct_link, construct_traits, construct_size, construct_stat_line, construct_hp, construct_attack_proficiency, construct_attacks, construct_extra_damage, construct_defense_proficiency, construct_saving_throws_proficiency, construct_immunities, construct_skill_proficiency, construct_speed, construct_senses])            
        log([construct_type_name, construct_link, construct_traits, construct_size, construct_stat_line, construct_hp, construct_attack_proficiency, construct_attacks, construct_extra_damage, construct_defense_proficiency, construct_saving_throws_proficiency, construct_immunities, construct_skill_proficiency, construct_speed, construct_senses])    
    
    return construct_output                
            
            
 
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
            attack_name_str += attack[0].strip()[:-1] + ";"
            attack_type_str += attack[1].strip() + ";"
            attack_damage_dice_str += attack[2].strip() + ";"
            attack_damage_type_str += attack[3].strip() + ";"
            
        attack_name_str = attack_name_str[:-1]
        attack_type_str = attack_type_str[:-1]
        attack_damage_dice_str = attack_damage_dice_str[:-1]
        attack_damage_type_str = attack_damage_type_str[:-1]
            
        for skill in ac[7]:
            skill_str += skill + ","
        
        skill_str = skill_str[:-1]
            
        organized_output.append(f"\"{ac[0]}\", \"{ac[1]}\", \"{ac[2]}\", \"{ac[3]}\", \"{attack_name_str}\", \"{attack_type_str}\", \"{attack_damage_dice_str}\", \"{attack_damage_type_str}\", \"{strength_str}\",\"{dexterity_str}\",\"{constitution_str}\", \"{intelligence_str}\",\"{wisdom_str}\",\"{charisma_str}\", {ac[6]}, \"{skill_str}\", \"{ac[8][:-1]}\", \"{ac[9]}\", \"{ac[10]}\", \"{ac[11]}\", \"{ac[12]}\"")
        log(f"Added \"{ac[0]}\", \"{ac[1]}\", \"{ac[2]}\", \"{ac[3]}\", \"{attack_name_str}\", \"{attack_type_str}\", \"{attack_damage_dice_str}\", \"{attack_damage_type_str}\", \"{strength_str}\",\"{dexterity_str}\",\"{constitution_str}\", \"{intelligence_str}\",\"{wisdom_str}\",\"{charisma_str}\", {ac[6]}, \"{skill_str}\", \"{ac[8]}\", \"{ac[9]}\", \"{ac[10]}\", \"{ac[11]}\", \"{ac[12]}\" to Organized Output")

    return organized_output

def organize_advanced_data():
    log("Getting Advanced Option Data")
    output = grab_advanced_option_data()

    organized_output = []

    log("Organizing Advanced Option Data")
    for option in output:
        full_option_str = "\""
        o = "\",\"".join(option)
        full_option_str += o + "\""
        organized_output.append(full_option_str)
        log(f"Adding {full_option_str} to Organzied Output")

    return organized_output

def organize_construct_companion_data():
    log("Getting Construct Data")
    output = grab_construct_companion_data()

    organized_output = []

    log("Organizing Construct Data")
    for option in output:
        full_option_str = "\""
        o = "\",\"".join(option)
        full_option_str += o + "\""
        organized_output.append(full_option_str)
        log(f"Adding {full_option_str} to Organzied Output")

    return organized_output