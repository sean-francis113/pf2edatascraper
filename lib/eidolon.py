from os import remove
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

import lib.db
from lib.helper import remove_tags, find_earliest_position, open_selenium, find_which_exists
from lib.log import log_text as log

url = "https://2e.aonprd.com/Eidolons.aspx?ID="
error_limit = 5
test_limit = 0

def upload_eidolon_data():
    log("Starting Eidolon Upload Preperation")
    eidolon_data, form_data = organize_eidolon_data()
    log("Preparation Done")

    log("Clearing Eidolon Table")
    conn, row_count, result = lib.db.query_database("DELETE FROM official_eidolons;", get_result=True, close_conn=False)

    log("Starting INSERT Process")
    for eidolon in eidolon_data:
        log("Inserting " + eidolon + " Into Database")
        conn = lib.db.query_database("INSERT INTO official_eidolons VALUES (" + eidolon + ");", connection=conn, close_conn=False)[0]

    log("Clearing Eidolon Table")
    conn, row_count, result = lib.db.query_database("DELETE FROM official_eidolon_forms;", get_result=True, close_conn=False)

    log("Starting INSERT Process")
    for form in form_data:
        log("Inserting " + form + " Into Database")
        conn = lib.db.query_database("INSERT INTO official_eidolon_forms VALUES (" + form + ");", connection=conn, close_conn=False)[0]

    log("Commiting Database Changes")
    conn.commit()
    log("Closing Connection")
    conn.close()
    
def grab_eidolon_data():
    global error_limit
    curr_error_num = 0

    eidolon_output = []
    form_output = []

    log("Starting to Grab Eidolon Data")
    log("Opening Browser")
    driver = open_selenium()

    i = 1

    while(True):
        eidolon_name = ""
        eidolon_link = f"{url}{i}"
        eidolon_traits = []
        eidolon_description = ""
        eidolon_traditions = []
        eidolon_size = ""
        eidolon_forms = []
        eidolon_skills = []
        eidolon_senses = ""
        eidolon_languages = ""
        eidolon_speed = ""
        eidolon_initial_ability = []
        eidolon_symbiosis_ability = []
        eidolon_transcendence_ability = []        

        log(f"Going to Page: {eidolon_link}")
        driver.get(f"{eidolon_link}")

        log("Getting Page Source")
        html = driver.page_source

        if html.find("Server Error in '/' Application.") > -1:
            log("Reached An Unknown Eidolon ID.")
            curr_error_num += 1
            if curr_error_num == error_limit:
                log("Ending Search.")
                break
            else:
                log(f"Reached Unknown Eidolon {curr_error_num} in a Row. Limit is {error_limit}")
                i += 1
                continue

        if curr_error_num > 0:
            log("Resetting Error Count")
            curr_error_num = 0

        log("Setting up BeautifulSoup with Source")
        soup = BeautifulSoup(html, "html.parser")
        
        log("Getting Container")
        container = soup.find(id="ctl00_RadDrawer1_Content_MainContent_DetailedOutput")
        html = str(container)
        
        log("Getting Eidolon Name")
        name_heading = container.find("h1")
        eidolon_name = name_heading.text.replace(" Eidolon", "")
        log(f"Found: {eidolon_name}")
        
        log("Getting Eidolon Traits")
        spans = container.find_all("span", {"class": "trait"})
        for span in spans:
            eidolon_traits.append(span.text)
        log(f"Found: {str(eidolon_traits)}")
                
        log("Getting Eidolon Description")        
        source_pos = html.find("<b>Source</b>")
        description_start_pos = html.find("<br>",source_pos) + len("<br>")
        if description_start_pos == len("<br>") - 1:
            description_start_pos = html.find("<br/>", source_pos) + len("<br/>")

        description_end_pos = html.find("<br>", description_start_pos)
        if description_end_pos == -1:
            description_end_pos = html.find("<br/>", description_start_pos)
            
        eidolon_description = html[description_start_pos:description_end_pos]
        eidolon_description = remove_tags(eidolon_description)
        log(f"Found: {eidolon_description}")
        
        log("Getting Eidolon Tradition(s)")
        tradition_start_pos = html.find("<b>Tradition</b>") + len("<b>Tradition</b>")
        tradition_end_pos = html.find("<br>", tradition_start_pos)
        if tradition_end_pos == -1:
            tradition_end_pos = html.find("<br/>", tradition_start_pos)
        tradition_str = remove_tags(html[tradition_start_pos:tradition_end_pos])
        eidolon_traditions = tradition_str.split(",")
        log(f"Found {str(eidolon_traditions)}")
        
        log("Getting Eidolon Size")
        size_start_pos = html.find("<b>Size</b>") + len("<b>Size</b>")
        size_end_pos = html.find("<br>", size_start_pos)
        if size_end_pos == -1:
            size_end_pos = html.find("<br/>", size_start_pos)
        eidolon_size = html[size_start_pos:size_end_pos]
        log(f"Found: {eidolon_size}")
        
        log("Getting Eidolon Forms")
        form_str = ""
        form_start_pos = html.find("<br>", size_end_pos + 1) + len("<br>")
        form_end_pos = 0
        if form_start_pos == len("<br>") - 1:
            form_start_pos = html.find("<br/>", size_end_pos + 1) + len("<br/>")
        
        while(html[form_start_pos:form_start_pos + 15].find("<b>Skills") == -1):
            form_end_pos = html.find("<br>", form_start_pos)
            if form_end_pos == -1:
                form_end_pos = html.find("<br/>", form_start_pos)
            
            form_str = html[form_start_pos:form_end_pos]
            full_form_str = form_str
            log(f"Form String: {form_str}")
            form_name = form_str[form_str.find("<b>") + len("<b>"):form_str.find("</b>")]
            form_str = form_str[form_str.find("</b>") + len("</b>"):]
            form_stats = form_str[:form_str.find(";")]
            form_stats = remove_tags(form_stats, "i")
            form_ac = form_str[form_str.find(";") + 1:]
            
            form_output.append([form_name, eidolon_name, form_stats, form_ac])
            
            form_start_pos += len(full_form_str) + 1
            form_end_pos = html.find("<br>", form_start_pos)
            if form_end_pos == -1:
                form_end_pos = html.find("<br/>", form_start_pos)
            
            log(f"Next Form String: {html[form_start_pos:form_start_pos + 15]}")
        log(f"Found: {str(eidolon_forms)}")
        
        log("Getting Eidolon Skills")
        skills_start_pos = html.find("<b>Skills</b>") + len("<b>Skills</b>")
        skills_end_pos = html.find("<br>", skills_start_pos)
        if skills_end_pos == -1:
            skills_end_pos = html.find("<br/>", skills_start_pos)
        skills_str = html[skills_start_pos:skills_end_pos]
        eidolon_skills = remove_tags(skills_str).split(",")        
        log(f"Found {str(eidolon_skills)}")
        
        log("Getting Eidolon Senses")
        senses_start_pos = html.find("<b>Senses</b>") + len("<b>Senses</b>")
        senses_end_pos = html.find("<br>", senses_start_pos)
        if senses_end_pos == -1:
            senses_end_pos = html.find("<br/>", senses_start_pos)
            
        eidolon_senses = remove_tags(html[senses_start_pos:senses_end_pos])        
        log(f"Found: {eidolon_senses}")
        
        log("Getting Eidolon Languages")
        languages_start_pos = html.find("<b>Languages</b>") + len("<b>Languages</b>")
        languages_end_pos = html.find("<br>", languages_start_pos)
        if (languages_end_pos == -1):
            languages_end_pos = html.find("<br/>", languages_start_pos)
            
        eidolon_languages = html[languages_start_pos:languages_end_pos]
        eidolon_languages = remove_tags(eidolon_languages)
        log(f"Found: {eidolon_languages}")
        
        log("Getting Eidolon Speed")
        speed_start_pos = html.find("<b>Speed</b>") + len("<b>Speed</b>")
        speed_end_pos = html.find("<hr>", speed_start_pos)
        if speed_end_pos == -1:
            speed_end_pos = html.find("<hr/>", speed_start_pos)
            
        eidolon_speed = html[speed_start_pos:speed_end_pos]
        log(f"Found: {eidolon_speed}")
        
        log("Getting Eidolon Abilities")
        abilities = container.find_all("h2")
        abilities_list = []
        for abil in abilities:
            ability_name = abil.text
            #if ability_name.find("7th") > -1:
                #ability_name = ability_name[:-3]
            #elif ability_name.find("17th") > -1:
                #ability_name = ability_name[:-4]
            
            for c in ability_name:
                if c.isnumeric():
                    ability_name = ability_name[:ability_name.index(c)]
                    break
                                                        
            ability_description_start_pos = html.find(f"{ability_name}</h2>") + len(f"{ability_name}</h2>")
            if ability_description_start_pos == len(f"{ability_name}</h2>") - 1:
                temp_start_pos = html.find(f"{ability_name}<span ") + len(f"{ability_name}<span ")
                ability_description_start_pos = html.find("</h2>", temp_start_pos) + len("</h2>")
            ability_description_end_pos = find_earliest_position(html.find("<h2", ability_description_start_pos), html.find("</span>", ability_description_start_pos), html.find("<h3", ability_description_start_pos))
            
            ability_description = html[ability_description_start_pos:ability_description_end_pos]
            ability_description = remove_tags(ability_description)
            
            abilities_list.append([ability_name, ability_description])
        
        eidolon_initial_ability = abilities_list[0]
        eidolon_symbiosis_ability = abilities_list[1]
        eidolon_transcendence_ability = abilities_list[2]
        
        log(f"Found: {abilities_list}")
        
        log([eidolon_name.strip(), eidolon_link.strip(), eidolon_description.strip(), 
             eidolon_traditions, eidolon_size.strip(), eidolon_skills, 
             eidolon_senses.strip(), eidolon_languages.strip(), eidolon_speed.strip(), 
             eidolon_initial_ability, eidolon_symbiosis_ability,
             eidolon_transcendence_ability])
        log(form_output)
        
        eidolon_output.append([eidolon_name.strip(), eidolon_link.strip(), eidolon_description.strip(), 
             eidolon_traditions, eidolon_size.strip(), eidolon_skills, 
             eidolon_senses.strip(), eidolon_languages.strip(), eidolon_speed.strip(), 
             eidolon_initial_ability, eidolon_symbiosis_ability,
             eidolon_transcendence_ability])

        if(test_limit > 0 and i == test_limit):
            break

        i += 1
        
    return eidolon_output, form_output

def organize_eidolon_data():
    log("Getting Eidolon Data")
    eidolon_output, form_output = grab_eidolon_data()
    
    organized_eidolon_output = []
    organized_form_output = []
    
    log("Organizing Eidolon Data (Without Forms)")
    for eidolon in eidolon_output:
        tradition_str = ""
        for t in eidolon[3]:
            tradition_str += t.strip() + ","
        tradition_str = tradition_str[:-1]
        
        skills_str = ""
        for s in eidolon[5]:
            skills_str += s.strip() + ","
        skills_str = skills_str[:-1]
        
        initial_abil_name = eidolon[9][0].strip()
        initial_abil_desc = eidolon[9][1].strip()
        symbi_abil_name = eidolon[10][0].strip()
        symbi_abil_desc = eidolon[10][1].strip()
        trans_abil_name = eidolon[11][0].strip()
        trans_abil_desc = eidolon[11][1].strip()
        
        organized_eidolon_output.append(f"\"{eidolon[0]}\",\"{eidolon[1]}\",\"{eidolon[2]}\",\"{tradition_str}\",\"{eidolon[4]}\",\"{skills_str}\",\"{eidolon[6]}\",\"{eidolon[7]}\",\"{eidolon[8]}\",\"{initial_abil_name}\",\"{initial_abil_desc}\",\"{symbi_abil_name}\",\"{symbi_abil_desc}\",\"{trans_abil_name}\",\"{trans_abil_desc}\"")
        log(f"Added \"{eidolon[0]}\",\"{eidolon[1]}\",\"{eidolon[2]}\",\"{tradition_str}\",\"{eidolon[4]}\",\"{skills_str}\",\"{eidolon[6]}\",\"{eidolon[7]}\",\"{eidolon[8]}\",\"{initial_abil_name}\",\"{initial_abil_desc}\",\"{symbi_abil_name}\",\"{symbi_abil_desc}\",\"{trans_abil_name}\",\"{trans_abil_desc}\" to Organized List")
        
    log("Organizing Form Data")
    for form in form_output:
        form_name = form[0].strip()
        eidolon_name = form[1].strip()
        ac_str = form[3].strip()
        final_stat_list = []
        strength_str = ""
        dexterity_str = ""
        constitution_str = ""
        intelligence_str = ""
        wisdom_str = ""
        charisma_str = ""
        
        stat_list = form[2].split(",")
        for stat in stat_list:
            stat = stat.strip()
            final_stat_list.append(stat.split(" ")[1])
        
        strength_str = final_stat_list[0]
        dexterity_str = final_stat_list[1]
        constitution_str = final_stat_list[2]
        intelligence_str = final_stat_list[3]
        wisdom_str = final_stat_list[4]
        charisma_str = final_stat_list[5]
        
        organized_form_output.append(f"\"{form_name}\",\"{eidolon_name}\",\"{strength_str}\",\"{dexterity_str}\",\"{constitution_str}\",\"{intelligence_str}\",\"{wisdom_str}\",\"{charisma_str}\",\"{ac_str}\"")
        log(f"Added \"{form_name}\",\"{eidolon_name}\",\"{strength_str}\",\"{dexterity_str}\",\"{constitution_str}\",\"{intelligence_str}\",\"{wisdom_str}\",\"{charisma_str}\",\"{ac_str}\" to Organized List")
        
    return organized_eidolon_output, organized_form_output