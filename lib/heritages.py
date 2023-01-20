from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

import lib.db
from lib.helper import remove_tags
from lib.log import log_text as log

url = "https://2e.aonprd.com/Ancestries.aspx"

def upload_heritage_data():
    log("Starting Heritage Upload Preperation")
    heritage_data = organize_heritage_data()
    log("Preparation Done")

    log("Clearing Table")
    conn, row_count, result = lib.db.query_database("DELETE FROM official_heritages;", get_result=True, close_conn=False)

    log("Starting INSERT Process")
    for heritage in heritage_data:
        log("Inserting " + heritage + " Into Database")
        conn = lib.db.query_database("INSERT INTO official_heritages VALUES (" + heritage + ");", connection=conn, close_conn=False)[0]

    log("Commiting Database Changes")
    conn.commit()
    log("Closing Connection")
    conn.close()

def grab_heritage_data():
    heritage_output = []

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
    container = soup.find(id="ctl00_RadDrawer1_Content_MainContent_DetailedOutput")
    log("Finding All Categories in Container")
    name_list = container.find_all("h2")

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
      ancestry_driver = webdriver.Chrome('./chromedriver.exe')
      ancestry_driver.get(output_link)
      log("Waiting for Page to Load")
      time.sleep(5)

      log("Getting Ancestry Page Source")
      ancestry_html = ancestry_driver.page_source
      log("Setting up BeautifulSoup with Page Source")
      ancestry_soup = BeautifulSoup(ancestry_html, "html.parser")

      log("Finding Sub Navigation")
      sub_nav_container = ancestry_soup.find(id="ctl00_RadDrawer1_Content_MainContent_SubNavigation")
      sub_nav_list = sub_nav_container.find_all("h2")
      log("Getting All Sub Navigation Headings")

      heritage_list_link = ""

      log("Searching Headings for Heritage Link")
      for nav in sub_nav_list:
          nav_links = nav.find_all("a")
          for n in nav_links:
              if n.get("href").startswith("Heritages.aspx"):
                  heritage_list_link = "https://2e.aonprd.com/" + n.get("href")
                  log(f"Found Heritage Link for {elements[0]}: {heritage_list_link}")

      log("Closing Ancestry Browser. Opening Heritage Browser")
      ancestry_driver.close()
      heritage_driver = webdriver.Chrome("./chromedriver.exe")
      heritage_driver.get(heritage_list_link)
      log("Waiting for Page to Load")
      time.sleep(5)

      log("Setting up BeautifulSoup with Page Source")
      heritage_html = heritage_driver.page_source
      heritage_soup = BeautifulSoup(heritage_html, "html.parser")

      log("Getting Heritage List Container")
      heritage_container = heritage_soup.find(id="ctl00_RadDrawer1_Content_MainContent_DetailedOutput")
      log("Getting All Headings")
      heritage_list = heritage_container.find_all("h2")

      heritage_name = ""
      heritage_link = ""
      heritage_summary = ""

      log("Starting Search for Heritages")
      i = 0
      for heritage in heritage_list:
          heritage_links = heritage.find_all("a")
          for l in heritage_links:
              if l.get("href").startswith("Heritages.aspx"):
                  heritage_name = l.text.split("\n")[0]

                  log("Found Heritage: " + heritage_name)
                  heritage_link = "https://2e.aonprd.com/" + l.get("href")
                  link_pos = heritage_html.find(l.get("href"))
                  print(f"Link Pos: {link_pos}")

                  versatile_heritage_pos = heritage_html.index("<h1 class=\"title\">Versatile Heritages</h1>")
                  half_human_heritage_pos = heritage_html.find("<h1 class=\"title\">Half-Human Heritages")

                  if half_human_heritage_pos == -1 or link_pos < half_human_heritage_pos:
                      start_pos = heritage_html.index("<br>", link_pos) + len("<br>")
                  else:
                      first_break_pos = heritage_html.index("<br>", link_pos) + len("<br>")
                      start_pos = heritage_html.index("<br>", first_break_pos) + len("<br>")

                  h3_pos = heritage_html.find("<h3", start_pos)
                  br_pos = heritage_html.find("<br>", start_pos)
                  end_pos = 0
                  print(f"H3 Pos: {h3_pos}; BR Pos: {br_pos}")

                  if h3_pos < br_pos and h3_pos != -1:
                      end_pos = h3_pos
                  elif br_pos < h3_pos and br_pos != -1:
                      end_pos = br_pos
                  elif br_pos != -1 and h3_pos == -1:
                      end_pos = br_pos
                  elif h3_pos != -1 and br_pos == -1:
                      end_pos = h3_pos

                  if end_pos > versatile_heritage_pos:
                      end_pos = versatile_heritage_pos

                  if start_pos > versatile_heritage_pos:
                      break

                  print(f"End Pos: {end_pos}; Next 50 Characters: {heritage_html[end_pos: end_pos + 50]}")

                  heritage_summary = heritage_html[start_pos:end_pos].strip()
                  print(heritage_summary)

                  if heritage_summary.find("<b>Source</b>") > -1:
                      end_pos += 3
                      temp_pos = heritage_html.find("<b>Source</b>", start_pos)
                      start_pos = heritage_html.find("<br>", temp_pos)
                      h3_pos = heritage_html.find("<h3", end_pos)
                      br_pos = heritage_html.find("<br>", end_pos)

                      if h3_pos < br_pos and h3_pos != -1:
                          end_pos = h3_pos
                      elif br_pos < h3_pos and br_pos != -1:
                          end_pos = br_pos

                      if end_pos > versatile_heritage_pos:
                          end_pos = versatile_heritage_pos

                      if start_pos > versatile_heritage_pos:
                          break

                      heritage_summary = heritage_html[start_pos:end_pos].strip()

                  if heritage_summary.find("PFS Note") > -1:
                      end_pos += 3
                      temp_pos = heritage_html.find("PFS Note", start_pos)
                      start_pos = heritage_html.find("<br>", temp_pos)
                      h3_pos = heritage_html.find("<h3", end_pos)
                      br_pos = heritage_html.find("<br>", end_pos)

                      if h3_pos < br_pos and h3_pos != -1:
                          end_pos = h3_pos
                      elif br_pos < h3_pos and br_pos != -1:
                          end_pos = br_pos

                      if end_pos > versatile_heritage_pos:
                          end_pos = versatile_heritage_pos

                      if start_pos > versatile_heritage_pos:
                          break

                      heritage_summary = heritage_html[start_pos:end_pos].strip()

                  heritage_summary = remove_tags(heritage_summary, tag_to_remove="h2", remove_inside=True)
                  heritage_summary = remove_tags(heritage_summary, tag_to_remove="table", remove_inside=True)
                  heritage_summary = remove_tags(heritage_summary, tag_to_remove="i")
                  heritage_summary = remove_tags(heritage_summary, tag_to_remove="u")
                  heritage_summary = remove_tags(heritage_summary, tag_to_remove="b")
                  heritage_summary = remove_tags(heritage_summary, tag_to_remove="a")

                  log(str([heritage_name, heritage_link, elements[0], heritage_summary]))
                  heritage_output.append([heritage_name, heritage_link, elements[0], heritage_summary])

    nav_container = soup.find(id="ctl00_RadDrawer1_Content_MainContent_Navigation")
    nav_links = nav_container.find_all("a")
    for link in nav_links:
        if link.get("href").endswith("Versatile=true"):
            versatile_heritage_link = "https://2e.aonprd.com/" + link.get("href")

            log("Opening Versatile Heritage Browser")
            versatile_heritage_driver = webdriver.Chrome("./chromedriver.exe")
            versatile_heritage_driver.get(versatile_heritage_link)
            log("Waiting for Page to Load")
            time.sleep(5)

            log("Setting up BeautifulSoup with Page Source")
            versatile_heritage_html = versatile_heritage_driver.page_source
            versatile_heritage_soup = BeautifulSoup(versatile_heritage_html, "html.parser")

            log("Getting Heritage List Container")
            versatile_heritage_container = versatile_heritage_soup.find(id="ctl00_RadDrawer1_Content_MainContent_DetailedOutput")
            log("Getting All Headings")
            versatile_heritage_list = versatile_heritage_container.find_all("h2")

            versatile_heritage_name = ""
            versatile_heritage_link = ""
            versatile_heritage_summary = ""

            log("Searching For Versatile Heritages")
            for heritage in versatile_heritage_list:
                vh_links = heritage.find_all("a")
                for l in vh_links:
                    if l.get("href").startswith("Ancestries.aspx"):
                        versatile_heritage_name = l.text.split("\n")[0]
                        log("Found Heritage: " + versatile_heritage_name)
                        vh_ancestry_link = "https://2e.aonprd.com/" + l.get("href")

                        log("Opening Versatile Heritage Ancestry Browser")
                        vh_ancestry_driver = webdriver.Chrome("./chromedriver.exe")
                        vh_ancestry_driver.get(vh_ancestry_link)
                        log("Waiting for Page to Load")
                        time.sleep(5)

                        log("Setting up BeautifulSoup with Page Source")
                        vh_ancestry_html = vh_ancestry_driver.page_source
                        vh_ancestry_soup = BeautifulSoup(vh_ancestry_html, "html.parser")

                        content_pos = vh_ancestry_soup.find(id="ctl00_RadDrawer1_Content_MainContent_DetailedOutput").sourcepos
                        vh_h1_pos = vh_ancestry_html.index("<h1 class=\"title\">Versatile Heritage</h1>", content_pos)

                        vh_h2_pos = vh_ancestry_html.index("</h2>", vh_h1_pos) + len("</h2>")
                        break_pos_1 = vh_ancestry_html.index("<br>", vh_h2_pos) + len("<br>")
                        break_pos_2 = vh_ancestry_html.index("<br>", break_pos_1) + len("<br>")
                        break_pos_3 = vh_ancestry_html.index("<br>", break_pos_2) + len("<br>")

                        end_pos = 0
                        span_pos = vh_ancestry_html.find("</span>", break_pos_3)
                        h3_pos =  vh_ancestry_html.find("<h3 class", break_pos_3)

                        if h3_pos == -1:
                            end_pos = span_pos
                        else:
                            if span_pos < h3_pos and span_pos != -1:
                                end_pos = span_pos
                            elif h3_pos < span_pos and h3_pos != -1:
                                end_pos = h3_pos

                        versatile_heritage_summary = vh_ancestry_html[break_pos_3:end_pos]
                        versatile_heritage_summary = remove_tags(versatile_heritage_summary, tag_to_remove="h2", remove_inside=True)
                        versatile_heritage_summary = remove_tags(versatile_heritage_summary, tag_to_remove="table", remove_inside=True)
                        versatile_heritage_summary = remove_tags(versatile_heritage_summary, tag_to_remove="i")
                        versatile_heritage_summary = remove_tags(versatile_heritage_summary, tag_to_remove="a")

                        log(str([versatile_heritage_name, vh_ancestry_link, "Versatile", versatile_heritage_summary]))
                        heritage_output.append([versatile_heritage_name, vh_ancestry_link, "Versatile", versatile_heritage_summary])


    return heritage_output

def organize_heritage_data():
    log("Getting Heritage Data")
    output = grab_heritage_data()

    organized_data = []

    log("Starting to Organize Heritage Data")
    for heritage in output:
        organized_data.append(f"\"{heritage[0]}\", \"{heritage[1]}\", \"{heritage[2]}\", \"{heritage[3]}\"")
        log(f"Added \"{heritage[0]}\", \"{heritage[1]}\", \"{heritage[2]}\", \"{heritage[3]}\" to Organized Data")

    return organized_data
