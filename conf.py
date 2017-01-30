import configparser

USE_VIRTUAL_DISPLAY = False
SEND_XMPP = False
SEND_APPOINTMENTS = False

TARGET_JID = None
BOT_JID = None
BOT_PASSWORD = None
USERNAME = None
PASSWORD = None

BASE_URL = None
CALENDAR_URL = None
CAL_SUFFIX = "Schedule/CalendarListViewEntry.aspx"


def read_config(filename):
    global TARGET_JID, BOT_JID, BOT_PASSWORD
    global USERNAME, PASSWORD
    global BASE_URL, CALENDAR_URL
    config = configparser.ConfigParser()
    config.read(filename)
    TARGET_JID = config['JABBER']['TARGET_JID']
    BOT_JID = config['JABBER']['BOT_JID']
    BOT_PASSWORD = config['JABBER']['BOT_PASSWORD']

    USERNAME = config['APP_PROVIDER']['username']
    PASSWORD = config['APP_PROVIDER']['password']
    BASE_URL = config['APP_PROVIDER']['base_url']
    CALENDAR_URL = BASE_URL + CAL_SUFFIX
