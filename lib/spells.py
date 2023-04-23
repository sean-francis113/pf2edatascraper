from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

import lib.db
from lib.helper import remove_tags, find_earliest_position, find_which_exists, open_selenium
from lib.log import log_text as log

spell_table_url = "https://2e.aonprd.com/Classes.aspx"
spell_list_url = "https://2e.aonprd.com/Spells.aspx?ID="
error_limit = 5
test_limit = 0

def upload_spell_data():
    log("Starting Spell Table Upload Preperation")
    spell_table_data = organize_spell_table_data()
    log("Preparation Done")

    log("Clearing Table")
    conn, row_count, result = lib.db.query_database("DELETE FROM official_spell_tables;", get_result=True, close_conn=False)

    log("Starting INSERT Process")
    for spell_table in spell_table_data:
        log("Inserting " + spell_table + " Into Database")
        conn = lib.db.query_database("INSERT INTO official_spell_tables VALUES (" + spell_table + ");", connection=conn, close_conn=False)[0]

    log("Commiting Database Changes")
    conn.commit()
    log("Closing Connection")
    conn.close()

    log("Starting Spell Upload Preperation")
    spell_data = organize_spell_data()
    log("Preparation Done")

    log("Clearing Table")
    conn, row_count, result = lib.db.query_database("DELETE FROM all_spells;", get_result=True, close_conn=False)

    log("Starting INSERT Process")
    for spell in spell_data:
        log("Inserting " + spell + " Into Database")
        conn = lib.db.query_database("INSERT INTO all_spells VALUES (" + spell + ");", connection=conn, close_conn=False)[0]

    log("Commiting Database Changes")
    conn.commit()
    log("Closing Connection")
    conn.close()

def grab_spell_table_data():
    spell_table_output = []

    driver = open_selenium()
    log("Opening Class Page")
    class_driver = open_selenium()
    log("Going to Page: " + spell_table_url)
    driver.get(spell_table_url)

    log("Getting Page Source")
    html = driver.page_source
    log("Setting up BeautifulSoup with Source")
    soup = BeautifulSoup(html, "html.parser")

    log("Finding Initial HTML Container")
    container = soup.find(id="ctl00_RadDrawer1_Content_MainContent_Navigation")
    log("Finding All Categories in Container")
    name_list = container.find_all("h1")

    for item in name_list:
        log("Getting All Links in Category")
        links = item.find_all("a")

        log("Grabbing Classes from Links")
        for link in links:
            if link.get("href").startswith("Classes.aspx"):
                class_name = link.text
                class_link = "https://2e.aonprd.com/" + link.get("href")
                log("Found " + class_name + " With the Following Link: " + class_link)

                if class_driver == None and len(spell_table_output) > 0:
                    return spell_table_output
                elif class_driver == None and len(spell_table_output) == 0:
                    return None

                class_driver.get(class_link)

                log("Getting Class Page Source")
                class_html = class_driver.page_source
                log("Preparing BeautifulSoup for Page Source")
                class_soup = BeautifulSoup(class_html, "html.parser")

                log("Finding Spell Table for " + class_name)
                spell_table = class_soup.find("table", {"class" : "inner spells-per-day"})
                if spell_table == None:
                    log(f"{class_name} Does Not Have a Spell Table. Moving On")
                    continue

                log("Getting All Table Rows")
                i = 1
                spell_table_rows = spell_table.find_all("tr")

                log("Searching Through Rows for Data")
                for row in spell_table_rows:
                    if i == 1 or i == 22:
                        log(f"Ignoring Row {i}")
                        i += 1
                        continue

                    rows_output = []

                    log("Grabbing All Data From Row")
                    row_data = row.find_all("td")

                    rows_output.append(class_name)
                    for data in row_data:
                        rows_output.append(remove_tags(data, tag_to_remove="td"))

                    if len(rows_output) < 13:
                        log("Adding Additional Slots for Missing Spell Levels")
                        difference = 13 - len(rows_output)
                        while difference > 0:
                            rows_output.append("0")
                            difference -= 1

                    log("Adding Row to Spell Table Output")
                    log(rows_output)
                    spell_table_output.append(rows_output)
                    i += 1

    return spell_table_output

def organize_spell_table_data():
    log("Getting Spell Table Data")
    spell_table_output = grab_spell_table_data()

    organized_output = []
    log("Starting to Organize Data")
    for st in spell_table_output:
        log(f"Adding {st} to Organized Output String")
        output_str = f"\"{st[0]}\", {st[1]}, {st[2]}, {st[3]}, {st[4]}, {st[5]}, {st[6]}, {st[7]}, {st[8]}, {st[9]}, {st[10]}, {st[11]}, {st[12]}"
        output_str = output_str.replace("—", "0")
        output_str = output_str.replace("†", "")
        output_str = output_str.replace("*", "")
        organized_output.append(output_str)
        log(f"Added \"{st[0]}\", {st[1]}, {st[2]}, {st[3]}, {st[4]}, {st[5]}, {st[6]}, {st[7]}, {st[8]}, {st[9]}, {st[10]}, {st[11]}, {st[12]} to Organized Output")

    return organized_output

def grab_spell_data():
    global error_limit
    curr_error_num = 0

    spell_output = []

    log("Starting to Grab Spells")
    driver = open_selenium()

    i = 1

    while(True):
        spell_name = ""
        spell_link = f"{spell_list_url}{i}"
        spell_level = ""
        spell_traditions = []
        spell_tradition_str = ""
        spell_actions = ""
        spell_summary = ""

        if driver == None and len(spell_output) > 0:
            return spell_output
        elif driver == None and len(spell_output) == 0:
            return None

        log(f"Going to Page: {spell_link}")
        driver.get(f"{spell_link}")

        log("Getting Page Source")
        html = driver.page_source

        if html.find("Server Error in '/' Application.") > -1:
            log("Reached An Unknown Spell ID.")
            curr_error_num += 1
            if curr_error_num == error_limit:
                log("Ending Search.")
                break
            else:
                log(f"Reached Unknown Spell {curr_error_num} in a Row. Limit is {error_limit}")
                i += 1
                continue

        if curr_error_num > 0:
            log("Resetting Error Count")
            curr_error_num = 0

        log("Setting up BeautifulSoup with Source")
        soup = BeautifulSoup(html, "html.parser")

        log("Finding Spell Name and Level")
        container = soup.find(id="ctl00_RadDrawer1_Content_MainContent_DetailedOutput")
        spell_name_level = container.find("h1")
        spell_name_level_pos = html.find("ctl00_RadDrawer1_Content_MainContent_DetailedOutput")
        print(spell_name_level_pos)
        spell_name_level_str = spell_name_level.text

        split_spell_name_level_str = spell_name_level_str.split(" ")
        spell_level = split_spell_name_level_str[-1]
        
        if(split_spell_name_level_str[-2][-5:] == "Spell" or split_spell_name_level_str[-2][-5:] == "Focus"):
            split_spell_name_level_str[-2] = split_spell_name_level_str[-2][:-5]
        elif(split_spell_name_level_str[-2][-7:] == "Cantrip"):
            split_spell_name_level_str[-2] = split_spell_name_level_str[-2][:-7]
            spell_level = "Cantrip"
            
        
        spell_name = " ".join(split_spell_name_level_str[:-1])

        #if spell_name_level_str.find("Spell") > -1 or spell_name_level.find("Focus") > -1:
            #spell_name = spell_name_level_str[:spell_name_level_str.find("Spell")]
            #spell_level = spell_name_level_str[spell_name_level_str.find("Spell"):].split(" ")[1]
        #elif spell_name_level_str.find("Cantrip") > -1:
            #spell_name = spell_name_level_str[:spell_name_level_str.find("Cantrip")]
            #spell_level = "Cantrip"

        log(f"Found: {spell_name}, Level {spell_level}")
        log("Finding Spell Tradition(s)")
        links = container.find_all("a")

        for l in links:
            if "Tradition=" in l.get("href"):
                spell_traditions.append(l.text)

        log(f"Found {str(spell_traditions)}")
        log("Setting Tradition List to String")
        for t in spell_traditions:
            spell_tradition_str += f"{t}, "

        spell_tradition_str = spell_tradition_str[:-2]

        log("Finding Number of Actions to Cast")
        exist_list = find_which_exists(html, html.find("<b>Cast</b>", spell_name_level_pos), "title=\"Free Action\"", "title=\"Reaction\"", "title=\"Single Action\"", "title=\"Two Actions\"", "title=\"Three Actions\"")
        print(exist_list)

        if len(exist_list) == 1:
            if "Single Action" in exist_list[0]:
                spell_actions = "1 Action"
            elif "Two Actions" in exist_list[0]:
                spell_actions = "2 Actions"
            elif "Three Actions" in exist_list[0]:
                spell_actions = "3 Actions"
            elif "Reaction" in exist_list[0]:
                spell_actions = "Reaction"
            elif "Free Action" in exist_list[0]:
                spell_actions = "Free"
        else:
            found_single = True
            found_double = True
            found_triple = True

            for e in exist_list:
                if "Single Action" in e:
                    found_single = True
                elif "Two Actions" in e:
                    found_double = True
                elif "Three Actions" in e:
                    found_triple = True

            if found_single and found_triple:
                spell_actions = "Variable (1-3)"
            elif found_single and found_double:
                spell_actions = "Variable (1-2)"
            elif found_double and found_triple:
                spell_actions = "Variable (2-3)"

        log(f"Found {spell_actions}")

        log("Finding Spell Summary")
        summary_start_pos = html.find("<hr>", spell_name_level_pos) + len("<hr>")
        print(f"Start Pos: {summary_start_pos}")
        print(f"Spell Name Pos: {spell_name_level_pos}")
        summary_end_pos = find_earliest_position(html.find("<br>", summary_start_pos),html.find("<hr>", summary_start_pos),html.find("<span", summary_start_pos),html.find("<h2", summary_start_pos), html.find("<h3", summary_start_pos),html.find("<ul", summary_start_pos))

        spell_summary = html[summary_start_pos:summary_end_pos]

        log(f"Found: {spell_summary}")
        spell_summary = remove_tags(spell_summary, tag_to_remove="h2", remove_inside=True)
        spell_summary = remove_tags(spell_summary, tag_to_remove="table", remove_inside=True)
        spell_summary = remove_tags(spell_summary)

        spell_output.append([spell_name, spell_link, spell_level, spell_tradition_str, spell_actions, spell_summary])
        log([spell_name, spell_link, spell_level, spell_tradition_str, spell_actions, spell_summary])

        if(test_limit > 0 and i == test_limit):
            break
        i += 1

    return spell_output

def organize_spell_data():
    log("Getting Spell Data")
    spell_output = grab_spell_data()
    organized_output = []
    log("Starting to Organize Data")

    for s in spell_output:
        log(f"Adding {s} to Organized Output String")
        organized_output.append(f"\"{s[0]}\", \"{s[1]}\", \"{s[2]}\", \"{s[3]}\", \"{s[4]}\", \"{s[5]}\"")
        log(f"Added \"{s[0]}\", \"{s[1]}\", \"{s[2]}\", \"{s[3]}\", \"{s[4]}\", \"{s[5]}\" to Organized Output")

    return organized_output
