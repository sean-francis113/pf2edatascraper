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
import lib.companions
import lib.eidolon
import lib.equipment
import lib.feats
import lib.helper
import lib.update

try:
    log_file = lib.log.open_log_file()

    if(lib.update.check_for_update()):
        lib.ancestry.upload_ancestry_data()
        lib.backgrounds.upload_background_data()
        lib.class_features.upload_features_data()
        lib.companions.upload_companion_data()
        lib.eidolon.upload_eidolon_data()
        lib.equipment.upload_equipment_data()
        lib.feats.upload_feat_data()
        lib.heritages.upload_heritage_data()
        lib.player_class.upload_class_data()
        lib.spells.upload_spell_data()

    lib.log.close_log_file()

except KeyboardInterrupt:
   print("Program terminated manually!")
   raise SystemExit
