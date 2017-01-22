#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import re
import datetime

from time import sleep

from selenium import webdriver
from selenium.webdriver.support import ui
from selenium.webdriver.common.keys import Keys

# local imports

import xmpp

from display import get_virtual_display, stop_virtual_display
from wodicalendar import Calendar
from conf import USE_VIRTUAL_DISPLAY
from conf import SEND_XMPP
from conf import LOGGER_NAME
import conf

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
    """ Assumes browser is open and login page loaded.
    Enters credential and submits them."""
    from conf import USERNAME, PASSWORD
    browser.get('https://app.wodify.com/WodifyAdminTheme/LoginEntry.aspx')
    uname = browser.find_element_by_id(USERNAME_ID)
    uname.send_keys(USERNAME)
    pword = browser.find_element_by_id(PASSWORD_ID)
    pword.send_keys(PASSWORD)
    sleep(1)
    print("submit")
    pword.send_keys(Keys.RETURN)
    print("beginning to wait...")
    wait.until(wod_finished_loading)
    print("wait ended")

# -------------------------- WOD


def parse_wod(browser):
    """ Assumes wod page is open.
    Parses wod, converts it to a text-based representation and returns it."""
    wodheader = browser.find_elements_by_id(WOD_HEADER_ELEMENT_ID)[0]
    date = wodheader.text
    wod_elem = browser.find_elements_by_id(WOD_BODY_ELEMENT_ID)[0]
    html = wod_elem.get_attribute('innerHTML')

    wod = html.replace("<div class=\"section_title\">", "<br>")
    wod = wod.replace("<div class=\"component_show_wrapper\">", "<br>")
    wod = wod.replace("<div class=\"component_comment\">", "")
    wod = re.sub("[<]\/?div.*?[>]", "<br>", wod)
    wod = wod.replace("<br><br>", "<br>")
    wod = wod.replace("<br><br><br>", "<br>")
    wod = re.sub("[\<]br?[\>]", "\n", wod)
    wod = re.sub("[\<].*?[\>]", "\n", wod)
    wod = wod.replace("&nbsp;", "")
    wod = re.sub("[\<].*?[\>]", "", wod)
    date = " ".join(date.split()[0:4])

    wod_date = date

    return wod, wod_date


##################
def main():
    """ Regular entry point """
    log = logging.Logger(LOGGER_NAME)

    conf.read_config("config.txt")

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
    if SEND_XMPP:
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
