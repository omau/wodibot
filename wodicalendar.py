from time import sleep
from collections import defaultdict
from datetime import datetime

import lxml
from lxml import etree

import conf
from schedule import ScheduleEntry
from schedule import AppointmentState
WEEKDAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY",
            "FRIDAY", "SATURDAY", "SUNDAY"]
THEME_PREFIX = "AthleteTheme_wt5_block_wtMainContent_wt8_"
DATE_PICK_ELEMENT_ID = THEME_PREFIX + "W_Utils_UI_wt211_block_wtDateInputFrom"
CLASS_TABLE_ELEMENT_ID = THEME_PREFIX + "wtClassTable"
SEP_DASHES = "----------------------"
TABLE_RECORDS_XPATH = "//table[@class='TableRecords']/tbody/tr"


def calendar_loaded(browser):
    return browser.find_elements_by_id(CLASS_TABLE_ELEMENT_ID)


class Calendar():
    def __init__(self, browser, wait):
        self.browser = browser
        self.wait = wait

    def open_calendar(self):
        self.browser.get(conf.CALENDAR_URL)
        print("waiting for calendar")
        self.wait.until(calendar_loaded)

    def open_date(self, cal_date):
        date_str = cal_date.strftime('%d/%m/%Y')
        # set calendar to today
        script_exec = self.browser.execute_script
        get_elem = "document.getElementById"

        script_exec(get_elem + "('{}').value = '{}';"
                    .format(DATE_PICK_ELEMENT_ID, date_str))

        script_exec(get_elem + "('{}').onchange();"
                    .format(DATE_PICK_ELEMENT_ID))

        sleep(4)
        self.wait.until(calendar_loaded)

    def parse_cal_row(self, row, date):
        assert len(row) == 9
        name = row[0][0][0].text

        if (len(list(row[1][0].itertext())) == 1):
            classload = list(row[1][0].itertext())[0]
        elif len(list(row[1][0].itertext())) == 5:
            reserved = list(row[1][0].itertext())[0]
            waitlisted = "(" + list(row[1][0].itertext())[4].strip() + ")"
            classload = reserved + " " + waitlisted
        elif len(list(row[1][0].itertext())) in [3, 4]:
            classload = list(row[1][0].itertext())[0]

        assert len(list(row[1][0].itertext())) in [1, 3, 4, 5]

        reserv_col = etree.tostring(row[2]).decode('utf-8')
        reserve_button_id = None
        if "Make Reservation" in reserv_col:
            state = AppointmentState.RESERVABLE
            left_index = reserv_col.find("id")+4
            right_index = reserv_col.find("tabindex")-2
            reserve_button_id = reserv_col[left_index:right_index]
        elif "has expired" in reserv_col or "have closed" in reserv_col:
            state = AppointmentState.EXPIRED
        elif "You have a" in reserv_col:
            state = AppointmentState.RESERVED
        elif "hours before class" in reserv_col:
            state = AppointmentState.FUTURE
        elif "CANCELLED" in classload:
            state = AppointmentState.CANCELLED
        else:
            state = AppointmentState.FULL

        program = row[4][0].text
        start_time = row[6][0][0].text
        end_time = row[7][0][0].text
        if len(row[8][0].getchildren()) != 0:
            coach = row[8][0][0].text
        else:
            coach = ""

        s = ScheduleEntry(name, classload, state,
                          program, date, start_time, end_time, coach, reserve_button_id)
        return s

    def is_day_descriptor(self, tr):
        return tr[0][0].tag == 'span'

    def get_by_days(self, cal_table):
        by_days = []

        current = [cal_table[0]]
        for row_index in range(1, len(cal_table)):
            row = cal_table[row_index]
            if self.is_day_descriptor(row):
                by_days += [current]
                current = [cal_table[row_index]]
            else:
                current += [row]

        by_days += [current]
        return by_days

    def parse_table(self):
        root = lxml.html.fromstring(self.browser.page_source)
        cal_table = root.cssselect("[id$='wtClassTable']")[0]
        cal_body = cal_table[1]

        classes = defaultdict(list)

        for one_day in self.get_by_days(cal_body):
            print(SEP_DASHES + " DAY SEPARATOR " + SEP_DASHES)
            cal_day = list(one_day[0][0][0].itertext())[1]
            cal_day = datetime.strptime(cal_day, "%d/%m/%Y").date()

            print("Day: ", cal_day)
            for row_index in range(1, len(one_day)):
                row = one_day[row_index]
                s = self.parse_cal_row(row, cal_day)
                classes[cal_day].extend([s])
        return classes
