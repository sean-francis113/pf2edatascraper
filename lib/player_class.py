from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

import lib.db
import lib.helper
from lib.log import log_text as log

url = "https://2e.aonprd.com/Classes.aspx"

def upload_class_data():
    log("Starting Class Upload Preperation")
    class_data = organize_class_data()
    log("Preparation Done")

    log("Clearing Table")
    conn, row_count, result = lib.db.query_database("DELETE FROM official_classes;", get_result=True, close_conn=False)

    log("Starting INSERT Process")
    for p_class in class_data:
        log("Inserting " + p_class + " Into Database")
        conn = lib.db.query_database("INSERT INTO official_classes VALUES (" + p_class + ");", connection=conn, close_conn=False)[0]

    log("Commiting Database Changes")
    conn.commit()
    log("Closing Connection")
    conn.close()

def grab_class_data():
    class_output = []

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

    log("Finding Initial HTML Container")
    container = soup.find(id="ctl00_RadDrawer1_Content_MainContent_Navigation")
    log("Finding All Categories in Container")
    name_list = container.find_all("h1")

    temp_output = []

    for item in name_list:
        log("Getting All Links in Category")
        links = item.find_all("a")

        log("Grabbing Classes from Links")
        for link in links:
            if link.get("href").startswith("Classes.aspx"):
                class_name = link.text
                class_link = "https://2e.aonprd.com/" + link.get("href")
                log("Found " + class_name + " With the Following Link: " + class_link)

                log("Opening Class Page")
                class_driver = webdriver.Chrome("./chromedriver.exe")
                class_driver.get(class_link)
                log("Waiting for Page to Load")
                time.sleep(5)

                log("Getting Class Page Source")
                class_html = class_driver.page_source
                log("Preparing BeautifulSoup for Page Source")
                class_soup = BeautifulSoup(class_html, "html.parser")
                class_soup = class_soup.prettify()

                log("Getting Key Ability")
                start_pos = class_html.find("Key Ability: ") + len("Key Ability: ")
                end_pos = class_html.find("</b>", start_pos)

                class_key_ability = class_html[start_pos:end_pos]
                log("Found: " + class_key_ability)

                log("Getting Class HP")
                start_pos = class_html.find("Hit Points: ", end_pos) + len("Hit Points: ")
                end_pos = class_html.find(" plus your", start_pos)

                class_hp = class_html[start_pos:end_pos]
                log("Found: " + class_hp)

                log("Getting Initial Proficiencies")
                prof_start_pos = class_html.find(">Initial Proficiencies</h1>")
                prof_end_pos = class_html.find(">Class Features</h1>")
                prof_html = class_html[prof_start_pos:prof_end_pos]
                proficiency_str_lines = prof_html.split("<br>")

                #Outputs As: [Perception, Fort, Ref, Will, Skills, Extra_Skill_Number, Simple, Martial, Advanced, Unarmed, Extra_Attacks, Light_Armor, Medium_Armor, Heavy_Armor, Unarmored, class_dc, spell_attack, spell_dc, spell_tradition]
                proficiency_list = []
                skill_list = ["Acrobatics", "Arcana", "Athletics", "Crafting", "Deception", "Diplomacy", "Intimidation", "Lore", "Medicine", "Nature", "Occultism", "Performance", "Religion", "Society", "Stealth", "Survival", "Thievery"]

                perception = "Untrained"
                fort = "Untrained"
                reflex = "Untrained"
                will = "Untrained"
                skills = ""
                extra_skill_num = "0"
                simple_wep = "Untrained"
                martial_wep = "Untrained"
                advanced_wep = "Untrained"
                unarmed_wep = "Untrained"
                extra_wep = "Untrained"
                extra_wep_list = []
                light_armor = "Untrained"
                med_armor = "Untrained"
                heavy_armor = "Untrained"
                unarmored = "Untrained"
                class_dc = "Untrained"
                spell_attack = "Untrained"
                spell_dc = "Untrained"
                spell_tradition = []

                for p in proficiency_str_lines:
                    if p is None:
                        log("Found an Empty Line. Moving On to Next Line")
                        continue

                    log("Grabbing Stats From Line: \"" + p + "\"")
                    p = lib.helper.remove_tags(p, remove_inside=True)
                    p = lib.helper.remove_tags(p, tag_to_remove="a")
                    p = p.strip()
                    log("Tagless Line: \"" + p + "\"")

                    log("Looking for Skills")
                    for skill in skill_list:
                        if skill in p and " or " not in p:
                            log("Found Skill")
                            skills += skill + ", "
                            log("Skill: " + skill)

                    if "Perception" in p:
                        log("Found Perception")
                        perception = p.split(" ")[0]
                        log("Perception (" + perception + ")")
                    elif "Fortitude" in p:
                        log("Found Fortitude")
                        fort = p.split(" ")[0]
                        log("Fortitude (" + fort + ")")
                    elif "Reflex" in p:
                        log("Found Reflex")
                        reflex = p.split(" ")[0]
                        log("Reflex (" + reflex + ")")
                    elif "Will" in p:
                        log("Found Will")
                        will = p.split(" ")[0]
                        log("Will (" + will + ")")
                    elif "additional skills" in p or "a number of skills" in p:
                        log("Found Additional Skills")
                        start_pos = p.find("equal to ") + len("equal to ")
                        end_pos = p.find(" plus your", start_pos)
                        extra_skill_num = int(p[start_pos:end_pos])
                        log("Extra Skills Number: " + str(extra_skill_num))
                    elif "simple weapons" in p:
                        log("Found Simple Weapons")
                        simple_wep = p.split(" ")[0]
                        log("Simple Weapons (" + simple_wep + ")")
                    elif "martial weapons" in p:
                        log("Found Martial Weapons")
                        martial_wep = p.split(" ")[0]
                        log("Martial Weapons (" + martial_wep + ")")
                        if "simple and martial weapons" in p:
                            log("Found Simple and Martial Weapons")
                            simple_wep = martial_wep
                            log("Simple and Martial Weapons (" + martial_wep + ")")
                    elif "advanced weapons" in p:
                        log("Found Advanced Weapons")
                        advanced_wep = p.split(" ")[0]
                        log("Advanced Weapons (" + advanced_wep + ")")
                    elif p.count(", ") > 1:
                        log("Found Extra Weapons")
                        extra_wep = p.split(" ")[0]
                        temp_extra_wep_list = p.split(", ")
                        i = 0
                        for w in temp_extra_wep_list:
                            split_wep = w.split(" ")
                            if len(split_wep) > 1:
                                if split_wep[-2]=="heavy" or split_wep[-2]=="light" or split_wep[-2]=="hand":
                                    extra_wep_list.append(split_wep[-2] + " " + split_wep[-1])
                                else:
                                    extra_wep_list.append(split_wep[-1])
                            else:
                                extra_wep_list.append(split_wep[-1])
                        log("Extra Weapon List: " + str(extra_wep_list))
                    elif "unarmed attacks" in p:
                        log("Found Unarmed Attacks")
                        unarmed_wep = p.split(" ")[0]
                        log("Unarmed Attacks (" + unarmed_wep + ")")
                    elif "light armor" in p:
                        log("Found Light Armor")
                        light_armor = p.split(" ")[0]
                        log("Light Armor (" + light_armor + ")")
                    elif "medium armor" in p:
                        log("Found Medium Armor")
                        med_armor = p.split(" ")[0]
                        log("Medium Armor (" + med_armor + ")")
                    elif "heavy armor" in p:
                        log("Found Heavy Armor")
                        heavy_armor = p.split(" ")[0]
                        log("Heavy Armor (" + heavy_armor + ")")
                    elif "all armor" in p:
                        log("Found All Armor")
                        light_armor = p.split(" ")[0]
                        med_armor = light_armor
                        heavy_armor = light_armor
                        log("All Armor (" + light_armor + ")")
                    elif "unarmored defense" in p:
                        log("Found Unarmored Defense")
                        unarmored = p.split(" ")[0]
                        log("Unarmored Defense (" + unarmored + ")")
                    elif "class DC" in p:
                        log("Found Class DC")
                        class_dc = p.split(" ")[0]
                        log("Class DC (" + class_dc + ")")
                    elif "spell attack" in p:
                        log("Found Spell Attack")
                        spell_attack = p.split(" ")[0]
                        log("Spell Attack (" + spell_attack + ")")
                        if "or" in p:
                            log("Found Multiple Spell Traditions")
                            tradition_split = p.split(" ")
                            or_index = tradition_split.index("or")
                            spell_tradition.append(tradition_split[or_index - 1])
                            spell_tradition.append(tradition_split[or_index + 1])
                            log("Spell Traditions: " + str(spell_tradition))
                        elif "arcane" in p:
                            log("Found Arcane Tradition")
                            spell_tradition.append("arcane")
                        elif "occult" in p:
                            log("Found Occult Tradition")
                            spell_tradition.append("occult")
                        elif "divine" in p:
                            log("Found Divine Tradition")
                            spell_tradition.append("divine")
                        elif "primal" in p:
                            log("Found Primal Tradition")
                            spell_tradition.append("primal")
                    elif "spell DC" in p:
                        log("Found Spell DC")
                        spell_dc = p.split(" ")[0]
                        log("Spell DC (" + spell_dc + ")")

                    #Special Cases
                    elif "alchemical bombs" in p:
                        log("Found Alchemical Bombs")
                        extra_wep = p.split(" ")[0]
                        extra_wep_list.append("alchemical bombs")
                        log("Alchemical Bombs (" + extra_wep + ")")
                    elif "favored weapon" in p:
                        log("Found Favored Weapon")
                        extra_wep = p.split(" ")[0]
                        extra_wep_list.append("favored weapon")
                        log("Favored Weapon (" + extra_wep + ")")
                    elif "firearms and crossbows" in p:
                        log("Found Firearms and Crossbows")
                        if "simple" in p:
                            extra_wep_list.append("simple firearms and crossbows (" + p.split(" ")[0] + ")")
                        elif "martial" in p:
                            extra_wep_list.append("martial firearms and crossbows (" + p.split(" ")[0] + ")")
                        elif "advanced" in p:
                            extra_wep_list.append("advanced firearms and crossbows (" + p.split(" ")[0] + ")")

                skills = skills[:len(skills) - 2]
                log("Adding All Stats to Proficiency List")
                proficiency_list = [perception, fort, reflex, will, skills, extra_skill_num, simple_wep, martial_wep, advanced_wep, unarmed_wep, extra_wep, extra_wep_list, light_armor, med_armor, heavy_armor, unarmored, class_dc, spell_attack, spell_dc, spell_tradition]
                log("Proficiency List: " + str(proficiency_list))
                class_driver.close()

                temp_output = [class_name, class_link, class_hp, class_key_ability]
                for p in proficiency_list:
                    temp_output.append(p)
                class_output.append(temp_output)

    driver.close()
    return class_output

def organize_class_data():
    log("Getting Class Data")
    output = grab_class_data()
    log("Recieved Class List")
    data_str = ""
    organized_output = []

    log("Starting to Organize Class List")
    for p_class in output:
        class_str = ""
        log("Organizing " + p_class[0] + " List")

        log(f"Adding Name, Link, HP, and Key Ability to String")
        class_str += f"\"{p_class[0]}\", \"{p_class[1]}\", {p_class[2]}, \"{p_class[3]}\","
        log(f"Added \"{p_class[0]}\", \"{p_class[1]}\", {p_class[2]}, \"{p_class[3]}\" to String")

        log(f"Adding Perception, Fortitude, Reflex, and Will Proficiencies to String")
        class_str += f"\"{p_class[4]}\", \"{p_class[5]}\", \"{p_class[6]}\", \"{p_class[7]}\","
        log(f"Added \"{p_class[4]}\", \"{p_class[5]}\", \"{p_class[6]}\", \"{p_class[7]}\" to String")

        log(f"Adding Skill Proficiencies and Number of Extra Skill Boosts to String")
        class_str += f"\"{p_class[8]}\", {p_class[9]},"
        log(f"Added \"{p_class[8]}\", {p_class[9]} to String")

        log(f"Adding Weapon Proficiencies to String")
        class_str += f"\"{p_class[10]}\", \"{p_class[11]}\", \"{p_class[12]}\", \"{p_class[13]}\","
        log(f"Added \"{p_class[10]}\", \"{p_class[11]}\", \"{p_class[12]}\", \"{p_class[13]}\" to String")

        log(f"Adding Any Extra Weapon Proficiencies to String")
        extra_wep_str = ""
        for wep in p_class[15]:
            extra_wep_str += wep + ", "
        extra_wep_str = extra_wep_str[:len(extra_wep_str) - 2]
        class_str += f"\"{p_class[14]}\", \"{extra_wep_str}\","
        log(f"Added \"{p_class[14]}\", \"{extra_wep_str}\" to String")

        log(f"Adding Armor Proficiencies to String")
        class_str += f"\"{p_class[16]}\", \"{p_class[17]}\", \"{p_class[18]}\", \"{p_class[19]}\","
        log(f"Added \"{p_class[16]}\", \"{p_class[17]}\", \"{p_class[18]}\", \"{p_class[19]}\" to String")

        log(f"Adding Class/Spell Proficiencies to String")
        class_str += f"\"{p_class[20]}\", \"{p_class[21]}\", \"{p_class[22]}\", "
        log(f"Added \"{p_class[20]}\", \"{p_class[21]}\", \"{p_class[22]}\", to String")

        log(f"Adding Spell Tradition to String")
        temp_str = ""
        for tradition in p_class[23]:
            temp_str += tradition.title() + ", "
        temp_str = temp_str[:len(temp_str) - 2]
        class_str += f"\"{temp_str}\""

        log("Adding Final String to Output")
        organized_output.append(class_str)

    log("Returning Output")
    for o in organized_output:
        print(str(o))
    return organized_output
