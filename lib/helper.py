from lib.log import log_text as log
from selenium import webdriver

def remove_tags(text, tag_to_remove="", remove_inside=False):
    tag_list = ["a", "h1", "h2", "h3", "span", "b", "i", "u", "hr", "hr/", "br", "br/", "li", "ul", "ol", "sup"]
    
    if type(text) != str:
        text = str(text)
        
    if tag_to_remove == "":
        for tag in tag_list:
            text = remove_tags(text, tag, remove_inside)
        return text               
    else:
        log("Removing \"" + tag_to_remove + "\" Tags From \"" + text + "\"")
        start_pos = text.find("<" + tag_to_remove)

        if start_pos == -1:
            log("Could Not Find Start Position. Checking for End Position")
            end_pos = text.find(f"</{tag_to_remove}>")
            if end_pos > -1:
                log("Found End Position. Removing.")
                text.replace(f"</{tag_to_remove}>", "")
            else:
                log("Found No End Position.")
            log("Returning.")
            return text

        log("Start: " + str(start_pos))
        end_pos = 0
        if remove_inside:
            end_pos = text.find("</" + tag_to_remove + ">", start_pos) + len("</" + tag_to_remove + ">")
            log("End: " + str(end_pos))
            text = text.replace(text[start_pos:end_pos], "", 1)
        else:
            end_pos = text.find(">", start_pos) + 1
            text = text.replace(text[start_pos:end_pos], "", 1)
            start_pos = text.find("</" + tag_to_remove + ">")
            end_pos = start_pos + len("</" + tag_to_remove + ">")
            text = text.replace(text[start_pos:end_pos], "", 1)

        if text.find("<" + tag_to_remove) != -1:
            return remove_tags(text, tag_to_remove, remove_inside)
        else:
            return text.strip()

def find_earliest_position(*args):
    if len(args) == 1:
        return args[0]
    elif len(args) == 0:
        return

    earliest_pos = 0

    for a in args:
        print(a)
        if a != -1:
            if earliest_pos == 0:
                earliest_pos = a
            elif a < earliest_pos:
                earliest_pos = a

    log(f"Earliest Position: {earliest_pos}")
    return earliest_pos

def find_which_exists(str, start, *args):
    if len(args) == 1:
        return args[0]
    elif len(args) == 0:
        return

    exist_list = []

    for a in args:
        if str.find(a, start) != -1:
            exist_list.append(a)

    return exist_list

def open_selenium():
    driver = None
    
    log("Opening Browser")
    try:
        driver = webdriver.Chrome("./chromedriver.exe")
        if driver != None:
            log("OS is Windows")
    except:
        driver = webdriver.Chrome("./chromedriver")
        if driver != None:
            log("OS is Linux")
    finally:
        log("Could Not Open Browser")
    
    return driver