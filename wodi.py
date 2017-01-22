#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.support import ui
from selenium.webdriver.common.keys import Keys
from time import sleep
import logging
import os
import re
import datetime

# local imports

import xmpp

from display import get_virtual_display, stop_virtual_display
from wodicalendar import Calendar
from conf import USE_VIRTUAL_DISPLAY
from conf import WODIFY_USERNAME, WODIFY_PASSWORD
from conf import SEND_XMPP
from conf import LOGGER_NAME

THEME_PREFIX = "AthleteTheme_wtLayoutNormal_block_"
WOD_HEADER_ELEMENT_ID = THEME_PREFIX + "wtTitle_wtTitleDiv"
WOD_BODY_ELEMENT_ID = THEME_PREFIX + "wtMainContent_wtComponentName"

LOGIN_PREFIX = "wtLayoutLogin_SilkUIFramework_wt11_block_"

USERNAME_ID = LOGIN_PREFIX + "wtUsername_wtUsername_wtUserNameInput"
PASSWORD_ID = LOGIN_PREFIX + "wtPassword_wtPassword_wtPasswordInput"

# ------------------------ browser


def get_browser():
    browser = webdriver.Firefox()
    browser.implicitly_wait(10)
    return browser


def wod_finished_loading(browser):
    return browser.find_elements_by_id(WOD_HEADER_ELEMENT_ID)


def login(browser, wait):
    browser.get('https://app.wodify.com/WodifyAdminTheme/LoginEntry.aspx')
    uname = browser.find_element_by_id(USERNAME_ID)
    uname.send_keys(WODIFY_USERNAME)
    pword = browser.find_element_by_id(PASSWORD_ID)
    pword.send_keys(WODIFY_PASSWORD)
    sleep(1)
    print("submit")
    pword.send_keys(Keys.RETURN)
    print("beginning to wait...")
    wait.until(wod_finished_loading)
    print("wait ended")

# -------------------------- WOD


def parse_wod(browser):
    wodheader = browser.find_elements_by_id(WOD_HEADER_ELEMENT_ID)[0]
    date = wodheader.text
    wod = browser.find_elements_by_id(WOD_BODY_ELEMENT_ID)[0]
    html = wod.get_attribute('innerHTML')

    a = html.replace("<div class=\"section_title\">", "<br>")
    b = a.replace("<div class=\"component_show_wrapper\">", "<br>")
    c = b.replace("<div class=\"component_comment\">", "")
    d = re.sub("[\<]\/?div.*?[\>]", "<br>", c)
    e = d.replace("<br><br>", "<br>")
    f = e.replace("<br><br><br>", "<br>")
    g = re.sub("[\<]br?[\>]", "\n", f)
    h = re.sub("[\<].*?[\>]", "\n", g)
    i = h.replace("&nbsp;", "")
    j = re.sub("[\<].*?[\>]", "", i)
    date = " ".join(date.split()[0:4])

    wod = j
    wod_date = date

    return wod, wod_date


##################
def main():

    log = logging.Logger(LOGGER_NAME)

    if USE_VIRTUAL_DISPLAY:
        log.info("Enabling virtual display")
        display = get_virtual_display()

    log.info("Starting browser")
    browser = get_browser()
    wait = ui.WebDriverWait(browser, 10)

    log.info("Logging in")

    login(browser, wait)

    #####################
    # parse today's wod
    #####################

    wod, wod_date = parse_wod(browser)

    #####################
    # send today's wod via xmpp
    #####################
    if (SEND_XMPP):
        xmpp_message = wod_date + "\n" + wod
        xmpp.send(xmpp_message)

    #####################
    # browse to calendar
    #####################
    cal = Calendar(browser, wait)
    cal.open_calendar()

    today = datetime.date.today()
    cal.open_date(today)

    cal.parse_table()

    browser.save_screenshot('screenie.png')
    browser.quit()
    if USE_VIRTUAL_DISPLAY:
        stop_virtual_display(display)

    os.system("killall firefox")
    os.system("killall Xvfb")


if __name__ == "__main__":
    main()
