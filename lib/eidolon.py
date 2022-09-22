from os import remove
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

import lib.db
from lib.helper import remove_tags, find_earliest_position, find_which_exists
from lib.log import log_text as log

url = "https://2e.aonprd.com/Eidolons.aspx?ID="
error_limit = 5

def upload_eidolon_data():
    log("Starting Eidolon Upload Preperation")
    eidolon_data = organize_eidolon_data()
    log("Preparation Done")

    log("Clearing Table")
    conn, row_count, result = lib.db.query_database("DELETE FROM official_eidolon;", get_result=True, close_conn=False)

    log("Starting INSERT Process")
    for eidolon in eidolon_data:
        log("Inserting " + eidolon + " Into Database")
        conn = lib.db.query_database("INSERT INTO official_eidolon VALUES (" + eidolon + ");", connection=conn, close_conn=False)[0]

    log("Commiting Database Changes")
    conn.commit()
    log("Closing Connection")
    conn.close()
    
def grab_eidolon_data():
    global error_limit
    curr_error_num = 0

    eidolon_output = []

    log("Starting to Grab Eidolon Data")

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
        eidolon_sybiosis_ability = []
        eidolon_transcendence_ability = []        

        log("Opening Browser")
        driver = webdriver.Chrome('./chromedriver.exe')
        log(f"Going to Page: {eidolon_link}")
        driver.get(f"{eidolon_link}")
        #log("Waiting for Page to Load")
        #time.sleep(5)

        log("Getting Page Source")
        html = driver.page_source

        if html.find("Server Error in '/' Application.") > -1:
            log("Reached An Unknown Feat ID.")
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
        eidolon_name = name_heading.text
        name_pos = name_heading.sourcepos
        log(f"Found: {eidolon_name}")
        
        log("Getting Eidolon Traits")
        spans = container.find_all("span", class_="trait")
        for span in spans:
            eidolon_traits.append(span["alt"].split(" ")[:-1])
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
        tradition_start_pos = html.find("<b>Tradition</b>", description_end_pos)
        if html.find("<u>", tradition_start_pos) > -1:
            tradition_list_start_pos = html.find("<u>", tradition_start_pos) + len("<u>")
            tradition_list_end_pos = html.find("</u>", tradition_list_start_pos)
            tradition_list_text = html[tradition_list_start_pos:tradition_list_end_pos]
            tradition_list_text = remove_tags(tradition_list_text, "a")
            eidolon_traditions = tradition_list_text.split(",")
            for t in eidolon_traditions:
                t = t.strip()
        log(f"Found {str(eidolon_traditions)}")
        
        log("Getting Eidolon Size")
        size_start_pos = html.find("<b>Size</b>", tradition_start_pos) + len("<b>Size</b>")
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
            log(f"Form String: {form_str}")
            form_name = form_str[form_str.find("<b>") + len("<b>"):form_str.find("</b>")]
            form_str = form_str[form_str.find("</b>") + len("</b>"):]
            form_stats = form_str[:form_str.find(";")]
            form_stats = remove_tags(form_stats, "i")
            form_ac = form_str[form_str.find(";") + 1:]
            
            eidolon_forms.append([form_name, form_stats, form_ac])
            form_start_pos = html.find("<br>", form_end_pos + 1) + len("<br>")   
            if form_start_pos == len("<br>") - 1:
                form_start_pos = html.find("<br/>", form_end_pos + 1) + len("<br/>")
            form_end_pos = html.find("<br>", form_start_pos)
            if form_end_pos == -1:
                form_end_pos = html.find("<br/>", form_start_pos) + len("<br/>")
            
            log(f"Next Form String: {html[form_start_pos:form_start_pos + 15]}")
        log(f"Found: {str(eidolon_forms)}")
        
        log("Getting Eidolon Skills")
        senses_start_pos = html.find("<b>Senses</b>", form_end_pos)
        if html.find("<u>", form_end_pos) > -1:
            skill_list_start_pos = html.find("<u>", form_end_pos) + len("<u>")
            skill_list_end_pos = html.find("</u>", skill_list_start_pos)
            while(skill_list_end_pos < senses_start_pos and skill_list_end_pos != -1):
                skill_list_text = html[skill_list_start_pos:skill_list_end_pos]
                skill_list_text = remove_tags(skill_list_text, "a")
                eidolon_skills.append(skill_list_text)
                skill_list_start_pos = html.find("<u>", skill_list_end_pos + 1) + len("<u>")
                skill_list_end_pos = html.find("</u>", skill_list_start_pos)
                
            for s in eidolon_skills:
                s = s.strip()
        log(f"Found {str(eidolon_skills)}")
        
        log("Getting Eidolon Senses")
        senses_start_pos += len("<b>Senses</b>")
        senses_end_pos = html.find("<br>", senses_start_pos)
        if senses_end_pos == -1:
            senses_end_pos = html.find("<br/>", senses_start_pos)
            
        eidolon_senses = remove_tags(html[senses_start_pos:senses_end_pos], "a")        
        log(f"Found: {eidolon_senses}")
        
        log("Getting Eidolon Languages")
        languages_start_pos = html.find("<b>Languages</b>", senses_end_pos) + len("<b>Languages</b>")
        languages_end_pos = html.find("<br>", languages_start_pos)
        if (languages_end_pos == -1):
            languages_end_pos = html.find("<br/>", languages_start_pos)
            
        eidolon_languages = html[languages_start_pos:languages_end_pos]
        log(f"Found: {eidolon_languages}")
        
        log("Getting Eidolon Speed")
        speed_start_pos = html.find("<b>Speed</b>", languages_end_pos)
        speed_end_pos = html.find("<br>", speed_start_pos)
        if speed_end_pos == -1:
            speed_end_pos = html.find("<br/>", speed_start_pos)
            
        eidolon_speed = html[speed_start_pos:speed_end_pos]
        log(f"Found: {eidolon_speed}")
        
        log([eidolon_name, eidolon_link, eidolon_description, 
             eidolon_traditions, eidolon_size, eidolon_forms, 
             eidolon_skills, eidolon_senses, eidolon_languages, eidolon_speed])

        i += 1

def organize_eidolon_data():
    pass