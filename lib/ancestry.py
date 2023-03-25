from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

import lib.db
from lib.log import log_text as log
from lib.helper import remove_tags, find_earliest_position, open_selenium

url = "https://2e.aonprd.com/Ancestries.aspx"

def upload_ancestry_data():
    log("Starting Ancestry Upload Preperation")
    ancestry_data = organize_ancestry_data()
    log("Preparation Done")

    log("Clearing Table")
    conn, row_count, result = lib.db.query_database("DELETE FROM official_ancestries;", get_result=True, close_conn=False)

    log("Starting INSERT Process")
    for ancestry in ancestry_data:
        log("Inserting " + ancestry + " Into Database")
        conn = lib.db.query_database("INSERT INTO official_ancestries VALUES (" + ancestry + ");", connection=conn, close_conn=False)[0]

    log("Commiting Database Changes")
    conn.commit()
    log("Closing Connection")
    conn.close()

def grab_ancestry_data():
  ancestry_output = []

  driver = open_selenium()
  log("Going to Page: " + url)
  driver.get(url)

  log("Getting Page Source")
  html = driver.page_source
  log("Setting up BeautifulSoup with Source")
  soup = BeautifulSoup(html, "html.parser")

  log("Finding Initial HTML Container")
  container = soup.find(id="ctl00_RadDrawer1_Content_MainContent_DetailedOutput")
  log("Finding All Categories in Container")
  name_list = container.find_all("h2")

  temp_output = []

  for item in name_list:
    log("Grabbing Name in Category")
    elements = item.text.split("\n")
    log("Found: " + elements[0])

    log("Getting All Links in Category")
    links = item.find_all("a")
    output_link = ""
    log("Finding Ancestry Page Link")
    for link in links:
      if link.get("href").startswith("Ancestries.aspx"):
        output_link = "https://2e.aonprd.com/" + link.get("href")
        log("Found: " + output_link)
        break

    log("Opening Ancestry Page")
    driver.get(output_link)

    log("Getting Ancestry Page Source")
    ancestry_html = driver.page_source

    log("Getting HP")
    hp_output = find_ancestry_stat(ancestry_html, "Hit Points</h2>", True, False)
    log("Found: " + hp_output + "\nGetting Size")

    size_output = find_ancestry_stat(ancestry_html, "Size</h2>", True, False)
    log("Found: " + size_output + "\nGetting Speed")

    speed_output = find_ancestry_stat(ancestry_html, "Speed</h2>", True, False)
    speed_log_str = ""
    if type(speed_output) is list:
        for s in speed_output:
            speed_log_str += s + ", "
        speed_log_str = speed_log_str[:-1]
    else:
        speed_log_str = speed_output
    log("Found: " + speed_log_str + "\nGetting Ability Boosts")

    ability_boost_output = find_ancestry_stat(ancestry_html, "Ability Boosts</h2>")
    boost_log_str = ""
    if ability_boost_output is not None:
        for ab in ability_boost_output:
            boost_log_str += ab + ", "
        boost_log_str = boost_log_str[:-1]
    else:
        boost_log_str = elements[0] + " Has No Specified Ability Boosts"
    log("Found: " + boost_log_str + "\nGetting Ability Flaws")

    ability_flaw_output = find_ancestry_stat(ancestry_html, "Ability Flaw(s)</h2>", True)
    flaws_log_str = ""
    if ability_flaw_output is not None:
        for af in ability_flaw_output:
            flaws_log_str += af + ", "
        flaws_log_str = flaws_log_str[:-1]
    else:
        flaws_log_str = elements[0] + " Has No Specified Ability Flaws"
    log("Found: " + flaws_log_str + "\nGetting Languages")

    languages_output = find_ancestry_stat(ancestry_html, "Languages</h2>", True)
    languages_log_str = ""
    if languages_output is not None:
        for l in languages_output:
            languages_log_str += l + ", "
        languages_log_str = languages_log_str[:-1]
    else:
        languages_log_str = elements[0] + " Has No Specified Languages"
    log("Found: " + languages_log_str + "\nGetting Ancestry Specials")
    specials_output = find_ancestry_specials(ancestry_html)

    specials_log_str = ""
    if specials_output is not None:
        for s in specials_output:
            specials_log_str += s[0] + ", " + s[1] + ", "
        specials_log_str = languages_log_str[:-1]
    else:
        specials_log_str = elements[0] + " Has No Specified Specials"
    log("Found: " + languages_log_str + "\nAdding Output To List")
    ancestry_output.append([elements[0], output_link, hp_output, size_output, speed_output, ability_boost_output, ability_flaw_output, languages_output, specials_output])


  log("Closing Ancestry Page\n")
  driver.close()
  return ancestry_output

def find_ancestry_stat(text, key, include_last=False, output_as_list=True):
  all_options = []

  if text.find(key) == -1:
      log("Could Not Find Key")
      return

  log("Getting Number of Stats to Grab")
  start_pos = text.index(key) + len(key)
  option_end_pos = text.find("<h2 class", start_pos)

  if option_end_pos == -1 or option_end_pos - start_pos == 1000:
    option_end_pos = text.find("</span", start_pos)

  num_of_options = text[start_pos:option_end_pos].count("<br>")

  if include_last == False: num_of_options -= 1
  log("Number of Stats: " + str(num_of_options))
  log("Grabbing Stats")
  i = 1
  while num_of_options > 0:
    log("Getting Stat " + str(i))
    log("Start Pos: " + str(start_pos))
    end_pos = text.find("<br>", start_pos)
    log("End Pos: " + str(end_pos))
    option_str = text[start_pos:end_pos]
    log("Stat: " + option_str)

    if option_str.find("<a") > -1:
      log("Trimming Stat")
      trim_start = option_str.find(">") + 1
      trim_end = option_str.find("<", trim_start)
      option_str = option_str[trim_start:trim_end]
      log("Final Stat: " + option_str)

    log("Adding Stat to List")
    all_options.append(option_str)
    log("Resetting Positioning for Next Stat")
    start_pos = end_pos + len("<br>")
    num_of_options -= 1

  if output_as_list:
    log("Returning Stats as List")
    return all_options
  else:
    if len(all_options) == 1:
      log("Returning Stat in First List Index")
      return all_options[0]
    elif len(all_options) == 0 or all_options is None:
      log("Stat Was Not In List... Returning Nothing")
      return None
    else:
      log("Stats Were Not Supposed to be In a List, but Must Be Returned as a List")
      return all_options

def find_ancestry_specials(ancestry_html):
  log("Setting Up BeautifulSoup to Grab Specials")
  ancestry_soup = BeautifulSoup(ancestry_html, "html.parser")
  ancestry_container = ancestry_soup.find(id="ctl00_RadDrawer1_Content_MainContent_DetailedOutput")

  log("Finding All Headings")
  heading_list = ancestry_container.find_all("h2")
  special_list = []

  for heading in heading_list:
    log("Adding " + heading.text + " to List")
    special_list.append(heading)

  log("Grabbing Last Three Headings")
  special_list = special_list[-3:]
  output_list = []
  summary_detail_list = []
  for special in special_list:
    log("Confirming Heading is an Ancestry Special")
    if special.text != "Languages" and special.text != "Ability Flaw(s)" and special.text != "Ability Boosts" and special.text != "Speed" and special.text.startswith("Table 1-1:") == False:
      log(special.text + " is an Ancestry Special. Adding to Final List")
      special_name = special.text
      special_summary = ""

      print(special)
      special_pos = ancestry_html.find(str(special))
      if special_pos == -1:
          special_pos = ancestry_html.find(f">{special.text}</")
      summary_start_pos = ancestry_html.find("</h2>", special_pos) + len("</h2>")
      h2_pos = ancestry_html.find("<h2 ", summary_start_pos)
      h3_pos = ancestry_html.find("<h3 ", summary_start_pos)
      span_pos = ancestry_html.find("</span>", summary_start_pos)
      summary_end_pos = 0

      summary_end_pos = find_earliest_position(h2_pos, h3_pos, span_pos)

      special_summary = ancestry_html[summary_start_pos:summary_end_pos]
      special_summary = remove_tags(special_summary, tag_to_remove="h2", remove_inside=True)
      special_summary = remove_tags(special_summary, tag_to_remove="table", remove_inside=True)
      special_summary = remove_tags(special_summary, tag_to_remove="i")
      special_summary = remove_tags(special_summary, tag_to_remove="u")
      special_summary = remove_tags(special_summary, tag_to_remove="b")
      special_summary = remove_tags(special_summary, tag_to_remove="a")

      output_list.append([special.text, special_summary])

  log("Returning Final List")
  return output_list

def organize_ancestry_data():
  log("Getting Ancestry Data")
  output = grab_ancestry_data()
  log("Recieved Ancestry List")
  data_str = ""
  organized_output = []

  log("Starting to Organize Ancestry List")
  for ancestry in output:
    log("Organizing " + ancestry[0] + " List")

    log("Adding Name, Link, and HP to Data String")
    data_str += "\"" + ancestry[0] + "\",\"" + ancestry[1] + "\"," + ancestry[2] + ","
    log(ancestry[0] + ", " + ancestry[1] + ", and " + ancestry[2] + " Added to Data String")

    log("Adding Size to Data String")
    size_log_str = ""
    if ancestry[3].find(" or ") > -1:
      log("Multiple Sizes Found. Grabbing First in Size List")
      end_pos = ancestry[3].find(" or ")
      data_str += "\"" + ancestry[3][:end_pos] + "\","
      size_log_str = ancestry[3][:end_pos]
    else:
      log("Only One Size Found")
      data_str += "\"" + ancestry[3] + "\","
      size_log_str = ancestry[3]
    log(size_log_str + " Added to Data String")

    log("Adding Speed to Data String")
    speed_log_str = ""
    if type(ancestry[4]) is list:
      data_str += "\""
      for speed in ancestry[4]:
        data_str += speed + ", "
        speed_log_str += speed + ", "
      data_str = data_str[:-1]
      data_str += "\","
    else:
      data_str += "\"" + ancestry[4] + "\","
      speed_log_str = ancestry[4]
    log(speed_log_str + " Added to Data String")

    log("Adding Ability Boosts and Flaws to Data String")
    start_index = len(data_str)
    found_str = False
    if ancestry[5] != None:
      for a in ancestry[5]:
        if a == "Strength":
          data_str += "\"Yes\","
          found_str = True
      if found_str == False:
        if ancestry[6] is not None:
          for a in ancestry[6]:
            if a == "Strength":
              data_str += "\"Flaw\","
              found_str = True
      if found_str == False:
        data_str += "\"No\","
    else:
      if ancestry[6] is not None:
        for a in ancestry[6]:
          if a == "Strength":
            data_str += "\"Flaw\","
            found_str = True
      if found_str == False:
        data_str += "\"No\","

    found_dex = False
    if ancestry[5] != None:
      for a in ancestry[5]:
        if a == "Dexterity":
          data_str += "\"Yes\","
          found_dex = True
      if found_dex == False:
        if ancestry[6] is not None:
          for a in ancestry[6]:
            if a == "Dexterity":
              data_str += "\"Flaw\","
              found_dex = True
      if found_dex == False:
        data_str += "\"No\","
    else:
      if ancestry[6] is not None:
        for a in ancestry[6]:
          if a == "Dexterity":
            data_str += "\"Flaw\","
            found_dex = True
      if found_dex == False:
        data_str += "\"No\","

    found_con = False
    if ancestry[5] != None:
      for a in ancestry[5]:
        if a == "Constitution":
          data_str += "\"Yes\","
          found_con = True
      if found_con == False:
        if ancestry[6] is not None:
          for a in ancestry[6]:
            if a == "Constitution":
              data_str += "\"Flaw\","
              found_con = True
      if found_con == False:
        data_str += "\"No\","
    else:
      if ancestry[6] is not None:
        for a in ancestry[6]:
          if a == "Constitution":
            data_str += "\"Flaw\","
            found_con = True
      if found_con == False:
        data_str += "\"No\","

    found_int = False
    if ancestry[5] != None:
      for a in ancestry[5]:
        if a == "Intelligence":
          data_str += "\"Yes\","
          found_int = True
      if found_int == False:
        if ancestry[6] is not None:
          for a in ancestry[6]:
            if a == "Intelligence":
              data_str += "\"Flaw\","
              found_int = True
      if found_int == False:
        data_str += "\"No\","
    else:
      if ancestry[6] is not None:
        for a in ancestry[6]:
          if a == "Intelligence":
            data_str += "\"Flaw\","
            found_int = True
      if found_int == False:
        data_str += "\"No\","

    found_wis = False
    if ancestry[5] != None:
      for a in ancestry[5]:
        if a == "Wisdom":
          data_str += "\"Yes\","
          found_wis = True
      if found_wis == False:
        if ancestry[6] is not None:
          for a in ancestry[6]:
            if a == "Wisdom":
              data_str += "\"Flaw\","
              found_wis = True
      if found_wis == False:
        data_str += "\"No\","
    else:
      if ancestry[6] is not None:
        for a in ancestry[6]:
          if a == "Wisdom":
            data_str += "\"Flaw\","
            found_wis = True
      if found_wis == False:
        data_str += "\"No\","

    found_cha = False
    if ancestry[5] != None:
      for a in ancestry[5]:
        if a == "Charisma":
          data_str += "\"Yes\","
          found_cha = True
      if found_cha == False:
        if ancestry[6] is not None:
          for a in ancestry[6]:
            if a == "Charisma":
              data_str += "\"Flaw\","
              found_cha = True
      if found_cha == False:
        data_str += "\"No\","
    else:
      if ancestry[6] is not None:
        for a in ancestry[6]:
          if a == "Charisma":
            data_str += "\"Flaw\","
            found_cha = True
      if found_cha == False:
        data_str += "\"No\","
    log(data_str[start_index:-1] + " Added to Data String")

    log("Adding Languages to Data String")
    languages_log_str = ""
    if ancestry[7] == "None":
      data_str += "\"Common\","
      languages_log_str = "Common"
    else:
      language_str = "\""
      for language in ancestry[7]:
        language_str += language + ", "
        languages_log_str += language + ", "
      language_str = language_str.strip()
      languages_log_str = languages_log_str.strip()
      languages_log_str = languages_log_str[:-1]
      language_str = language_str[:-1]
      data_str += language_str + "\","
    log(languages_log_str + " Added to Data String")

    log("Adding Ancestry Specials to Data String")
    special_log_str = ""
    special_count = len(ancestry[8])
    for special in ancestry[8]:
      data_str += "\"" + special[0] + "\", \"" + special[1] + "\","
      special_log_str += special[0] + ", " + special[1] + ", "

    if special_count < 3:
        while 3 - special_count > 0:
            data_str += "\"\",\"\","
            special_count += 1

    data_str = data_str[:-1]
    log(special_log_str.strip()[:-1] + " Added to Data String")

    log("Adding Data String to Final List")
    organized_output.append(data_str)
    data_str = ""

  log("Returning Final List")
  return organized_output
