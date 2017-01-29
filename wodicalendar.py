from time import sleep
from collections import defaultdict
from datetime import datetime

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
        tds = row.find_elements_by_xpath("td")
        assert len(tds) == 9
        name = tds[0].text
        classload = tds[1].text.replace("\n", "")
        reserv_col = tds[2].get_attribute('innerHTML')
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

        program = tds[4].text
        start_time = tds[6].text
        end_time = tds[7].text
        coach = tds[8].text

        s = ScheduleEntry(name, classload, state,
                          program, date, start_time, end_time, coach, reserve_button_id)
        return s

    def is_day_descriptor(self, row):
        is_day = False
        first_col = row.find_elements_by_xpath("td")[0].text
        for day in WEEKDAYS:
            if day in first_col:
                is_day = True
        return is_day

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
        cal_table = self.browser.find_elements_by_xpath(TABLE_RECORDS_XPATH)

        classes = defaultdict(list)

        for one_day in self.get_by_days(cal_table):
            print(SEP_DASHES + " DAY SEPARATOR " + SEP_DASHES)
            cal_day = one_day[0].find_elements_by_xpath("td")[0].text
            cal_day = cal_day.split("\n")[1]
            cal_day = datetime.strptime(cal_day, "%d/%m/%Y").date()

            print("Day: ", cal_day)
            for row_index in range(1, len(one_day)):
                row = one_day[row_index]
                s = self.parse_cal_row(row, cal_day)
                classes[cal_day].extend([s])
        return classes
