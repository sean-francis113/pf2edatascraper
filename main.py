from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

import lib.ancestry
import lib.db
import lib.log
import lib.player_class
import lib.heritages
import lib.backgrounds
import lib.class_features
import lib.spells

try:
    log_file = lib.log.open_log_file()

    lib.companions.upload_companion_data()

    lib.log.close_log_file()

except KeyboardInterrupt:
   print("Program terminated manually!")
   raise SystemExit
