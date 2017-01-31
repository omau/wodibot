#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import re
import datetime
import pickle

from time import sleep
from datetime import timedelta
from collections import defaultdict

from selenium import webdriver
from selenium.webdriver.support import ui
from selenium.webdriver.common.keys import Keys

# local imports

import xmpp

from logger import prepare_logger
from display import get_virtual_display, stop_virtual_display
from wodicalendar import Calendar
from conf import USE_VIRTUAL_DISPLAY
from conf import SEND_XMPP
from conf import SEND_APPOINTMENTS
from schedule import AppointmentState
import conf

THEME_PREFIX = "AthleteTheme_wtLayoutNormal_block_"
WOD_HEADER_ELEMENT_ID = THEME_PREFIX + "wtTitle_wtTitleDiv"
WOD_BODY_ELEMENT_ID = THEME_PREFIX + "wtMainContent_wtComponentName"

USERNAME_ID = "wtUserNameInput"
PASSWORD_ID = "wtPasswordInput"

ID_ENDS_WITH = "[id$='{}']"

USERNAME_SELECTOR = ID_ENDS_WITH.format(USERNAME_ID)
PASSWORD_SELECTOR = ID_ENDS_WITH.format(PASSWORD_ID)

LOGIN_URL = "https://app.wodify.com/WodifyAdminTheme/LoginEntry.aspx"
# ------------------------ browser


def get_browser():
    browser = webdriver.Firefox()
    browser.implicitly_wait(10)
    return browser


def wod_finished_loading(browser):
    return browser.find_elements_by_id(WOD_HEADER_ELEMENT_ID)


def login(browser, wait):
    log = logging.getLogger(__name__)
    """ Assumes browser is open and login page loaded.
    Enters credential and submits them."""
    log.info("Loading main page")
    from conf import USERNAME, PASSWORD
    browser.get(LOGIN_URL)
    log.info("Entering credentials")
    uname = browser.find_element_by_css_selector(USERNAME_SELECTOR)
    uname.send_keys(USERNAME)
    pword = browser.find_element_by_css_selector(PASSWORD_SELECTOR)
    pword.send_keys(PASSWORD)
    sleep(1)
    log.info("Submitting")
    pword.send_keys(Keys.RETURN)
    wait.until(wod_finished_loading)

# -------------------------- WOD


def parse_wod(browser):
    log = logging.getLogger(__name__)
    log.info("Parsing WoD...")
    """ Assumes wod page is open.
    Parses wod, converts it to a text-based representation and returns it."""
    wodheader = browser.find_elements_by_id(WOD_HEADER_ELEMENT_ID)[0]
    date = wodheader.text
    wod_elem = browser.find_elements_by_id(WOD_BODY_ELEMENT_ID)[0]
    html = wod_elem.get_attribute('innerHTML')
    print("wod_html=", html)

    wod = html.replace("<div class=\"section_title\">", "<br>")
    wod = wod.replace("<div class=\"component_show_wrapper\">", "<br>")
    wod = wod.replace("<div class=\"component_comment\">", "\n")
    wod = re.sub("[<]\/?div.*?[>]", "<br>", wod)
    wod = wod.replace("<br><br>", "<br>")
    wod = wod.replace("<br><br><br>", "<br>")
    wod = re.sub("[\<]br?[\>]", "\n", wod)
    wod = re.sub("[\<].*?[\>]", "\n", wod)
    wod = wod.replace("&nbsp;", "")
    wod = re.sub("[\<].*?[\>]", "", wod)
    wod = wod.replace("\n\n\n", "\n\n")
    date = " ".join(date.split()[0:4])

    wod_date = date

    log.info("Finished Parsing WoD.")
    return wod, wod_date


def handle_disappeared(entry, past_schedule):
    print("Entry " + entry.get_basic_description() +
          " no longer exists, removing...")
    past_schedule[entry.date].remove(entry)


def handle_existing(entry, current_classes, potential_appointments):
    found = False
    for current_entry in current_classes[entry.date]:
        if current_entry == entry:
            found = True
            reserve = entry.update(current_entry)
            assert (entry.__str__() == current_entry.__str__())
            if reserve:
                potential_appointments += [current_entry]
    assert(found)


def handle_new(entry, past_schedule, potential_appointments):
    past_schedule[entry.date].extend([entry])
    print("Found new entry "+entry.get_basic_description())
    if entry.appointment_state == AppointmentState.RESERVABLE:
        potential_appointments += [entry]


def remove_old_classes(past_schedule):
    today = datetime.date.today()
    dates_to_remove = []

    for class_date in past_schedule.keys():
        if class_date < today:
            dates_to_remove += [class_date]
    for class_date in dates_to_remove:
        del past_schedule[class_date]

    return past_schedule


def update_classes_history(current_classes, potential_appointments):
    past_schedule = pickle.load(open("sched.p", "rb"))
    assert past_schedule is not None
    assert type(past_schedule) == defaultdict
    current_dates = set(current_classes.keys())

    for date in current_dates:
        past_list = past_schedule[date]

        for entry in past_list:
            if entry not in current_classes[date]:
                # found event in history that is not in current_classes
                # so it is either expired or cancelled
                handle_disappeared(entry, past_schedule)
            else:
                handle_existing(entry, current_classes, potential_appointments)

        for entry in current_classes[date]:
            if entry in past_list:
                # already treated in above case
                continue
            else:
                handle_new(entry, past_schedule, potential_appointments)

    past_schedule = remove_old_classes(past_schedule)
    pickle.dump(past_schedule, open("sched.p", "wb"))
    return past_schedule


def is_in_appointment_list(app):
    if app.name.strip() == "08:00 SMCM" and app.weekday in ["Monday", "Friday"]:
        return True
    if app.name.strip() == "09:00 WOD" and app.weekday == "Saturday":
        return True
    if app.name.strip() == "08:00 Weightlifting" and app.weekday == "Wednesday":
        return True
    if app.name.strip() == "18:00 WOD" and app.weekday == "Wednesday":
        return True
    return False


def make_appointments(browser, potential_appointments, xmpp):
    for app in potential_appointments:
        print("Found new possible appointment:", app.get_basic_description())
        if is_in_appointment_list(app):
            app.make_appointment(browser)
            xmpp_message = "Created appointment for {}".format(app.get_basic_description())
            print(xmpp_message)
            if SEND_XMPP:
                xmpp.send(xmpp_message)
    potential_appointments.clear()


def run_tasks(browser):

    wait = ui.WebDriverWait(browser, 10)

    login(browser, wait)

    #####################
    # parse today's wod
    #####################

    wod, wod_date = parse_wod(browser)

    last_wod = pickle.load(open("lastwod.p", "rb"))
    if last_wod == (wod_date+wod):
        same_wod = True
    else:
        same_wod = False
    #####################
    # send today's wod via xmpp
    #####################
    if SEND_XMPP and not same_wod:
        xmpp_message = wod_date + "\n" + wod
        xmpp.send(xmpp_message)

    pickle.dump(wod_date+wod, open("lastwod.p", "wb"))
    #####################
    # browse to calendar
    #####################
    cal = Calendar(browser, wait)
    cal.open_calendar()

    #####################
    # read next 7 days of classes
    #####################
    today = datetime.date.today()
    cal.open_date(today)

    potential_appointments = []

    classes = cal.parse_table()

    update_classes_history(classes, potential_appointments)
    make_appointments(browser, potential_appointments, xmpp)
    #####################
    # read next 7 days of classes
    #####################
    next_week = today + timedelta(weeks=1)
    cal.open_date(next_week)

    classes = cal.parse_table()
    schedule = update_classes_history(classes, potential_appointments)
    make_appointments(browser, potential_appointments, xmpp)

    if SEND_APPOINTMENTS:
        send_next_appointments(schedule)

##################


def send_next_appointments(schedule):
    app_str = "Your next appointments: \n"
    for date in schedule:
        class_list = schedule[date]
        for entry in class_list:
            if entry.appointment_state == AppointmentState.RESERVED:
                app_str += entry.get_basic_description()
                app_str += "\n---------------------\n"
    if SEND_XMPP:
        xmpp.send(app_str)


def main():
    """ Regular entry point """

    prepare_logger()
    log = logging.getLogger(__name__)
    conf.read_config("config.txt")

    if USE_VIRTUAL_DISPLAY:
        log.info("Enabling virtual display")
        display = get_virtual_display()
    else:
        log.info("Not using virtual display")

    browser = get_browser()

    try:
        run_tasks(browser)
    finally:
        browser.quit()
        if USE_VIRTUAL_DISPLAY:
            stop_virtual_display(display)


if __name__ == "__main__":
    main()
