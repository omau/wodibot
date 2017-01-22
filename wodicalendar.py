from time import sleep

import conf
from schedule import ScheduleEntry

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

        sleep(2)
        self.wait.until(calendar_loaded)

    def parse_cal_row(self, row, date):
        tds = row.find_elements_by_xpath("td")
        assert len(tds) == 9
        name = tds[0].text.encode('utf-8')
        classload = tds[1].text
        can_make_appointment = "UNKNOWN"

        reserv_col = tds[2].get_attribute('innerHTML')
        if "Make Reservation" in reserv_col:
            can_make_appointment = "YES"
        elif "has expired" in reserv_col:
            can_make_appointment = "NO"
        elif "You have a" in reserv_col:
            can_make_appointment = "ALREADY RESERVED"
        else:
            can_make_appointment = "NO"
        cancel_col = tds[3].get_attribute('innerHTML')
        if "Cancel Reservation" in cancel_col:
            can_cancel = "YES"
        else:
            can_cancel = "NO"

        program = tds[4].text.encode('utf-8')
        start_time = tds[6].text.encode('utf-8')
        end_time = tds[7].text.encode('utf-8')
        coach = tds[8].text.encode('utf-8')

        s = ScheduleEntry(name, classload, can_make_appointment, can_cancel,
                          program, date, start_time, end_time, coach)
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
        for one_day in self.get_by_days(cal_table):
            print(SEP_DASHES + " DAY SEPARATOR " + SEP_DASHES)
            cal_day = one_day[0].find_elements_by_xpath("td")[0].text
            cal_day = cal_day.encode('utf-8')

            print("Day: ", cal_day)
            for row_index in range(1, len(one_day)):
                row = one_day[row_index]
                s = self.parse_cal_row(row, cal_day)
                print(s)
