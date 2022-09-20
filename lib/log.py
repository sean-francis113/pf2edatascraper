import os
import datetime
from os.path import exists
from datetime import date

folder_path = "./logs/"
file_path = ""
log_file = None

def open_log_file(path_to_folder=folder_path, file_mode="a"):
    global log_file

    file_path = path_to_folder + "log_" + date.today().strftime("%b_%d_%Y") + ".txt"
    print("Trying to Open Log File \"" + file_path + "\"")

    if log_file is not None and check_file_status() == False:
        log_file.close()

    if exists(file_path):
        log_file = open(file_path, file_mode)
        return log_file
    else:
        f = open(file_path, "x")
        f.close()
        log_file = open(file_path, file_mode)
        return log_file

def log_text(text, close_file=True):
    global log_file

    if log_file is None:
        open_log_file()

    if type(text) != str:
        text = str(text)

    if text[-1] != ".":
        text += "."

    text = "[" + datetime.datetime.now().strftime("%H:%M:%S") + "]: " + text

    print(text)
    log_file.write(text + "\n")

def check_file_status():
    try:
        os.rename(file_path, file_path)
        return True #File is Closed
    except OSError:
        return False #File is Open

def close_log_file():
    global log_file

    log_text("Closing Log File")
    log_file.close()
