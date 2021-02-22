# SPDX-FileCopyrightText: 2020 Tim C, written for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

import wifi
import ssl
import socketpool
import adafruit_requests
from adafruit_progressbar import ProgressBar
from adafruit_magtag.magtag import MagTag


magtag = MagTag()


# Add a secrets.py to your filesystem that has a dictionary called secrets with "ssid" and
# "password" keys with your WiFi credentials. DO NOT share that file or commit it into Git or other
# source control.
# pylint: disable=no-name-in-module,wrong-import-order
try:
    from secrets import secrets
except ImportError:
    print("Credentials and tokens are kept in secrets.py, please add them there!")
    raise

# Get our username, key and desired timezone
aio_username = secrets["aio_username"]
aio_key = secrets["aio_key"]
location = secrets.get("timezone", None)
TIME_URL = (
    "https://io.adafruit.com/api/v2/%s/integrations/time/strftime?x-aio-key=%s"
    % (aio_username, aio_key)
)
TIME_URL += "&fmt=%25H%3A%25M"


print("Connecting to %s" % secrets["ssid"])
wifi.radio.connect(secrets["ssid"], secrets["password"])
print("Connected to %s!" % secrets["ssid"])

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

endpoint = (
    "https://covid.cdc.gov/covid-data-tracker/COVIDData/getAjaxData?id=vaccination_data"
)

# set progress bar width and height relative to board's display
BAR_WIDTH = (magtag.graphics.display.width // 2) - 10
BAR_HEIGHT = 13

NY_BAR_X = magtag.graphics.display.width // 4 - BAR_WIDTH // 2
US_BAR_X = (magtag.graphics.display.width // 4) * 3 - (BAR_WIDTH // 2)
DOSE1_BAR_Y = 66
DOSE2_BAR_Y = 81

dose1_ny_progress_bar = ProgressBar(
    NY_BAR_X,
    DOSE1_BAR_Y,
    BAR_WIDTH,
    BAR_HEIGHT,
    1.0,
    bar_color=0x999999,
    outline_color=0x000000,
)
dose1_us_progress_bar = ProgressBar(
    US_BAR_X,
    DOSE1_BAR_Y,
    BAR_WIDTH,
    BAR_HEIGHT,
    1.0,
    bar_color=0x999999,
    outline_color=0x000000,
)
dose2_ny_progress_bar = ProgressBar(
    NY_BAR_X,
    DOSE2_BAR_Y,
    BAR_WIDTH,
    BAR_HEIGHT,
    1.0,
    bar_color=0x999999,
    outline_color=0x000000,
)
dose2_us_progress_bar = ProgressBar(
    US_BAR_X,
    DOSE2_BAR_Y,
    BAR_WIDTH,
    BAR_HEIGHT,
    1.0,
    bar_color=0x999999,
    outline_color=0x000000,
)

# name
magtag.add_text(
    text_font="fonts/leaguespartan18.bdf",
    text_position=(
        (magtag.graphics.display.width // 2) - 1,
        20,
    ),
    text_anchor_point=(0.5, 0.5),
)

# NY Percent
magtag.add_text(
    text_font="fonts/leaguespartan18.bdf",
    text_position=(
        (magtag.graphics.display.width // 4) - 1,
        45,
    ),
    text_anchor_point=(0.5, 0.5),
)

# US Percent
magtag.add_text(
    text_font="fonts/leaguespartan18.bdf",
    text_position=(
        ((magtag.graphics.display.width // 4) - 1) * 3,
        45,
    ),
    text_anchor_point=(0.5, 0.5),
)

# Date
magtag.add_text(
    text_font="fonts/leaguespartan11.bdf",
    text_position=(
        (magtag.graphics.display.width // 2) - 1,
        (magtag.graphics.display.height) - 8,
    ),
    text_anchor_point=(0.5, 1.0),
)


magtag.graphics.splash.append(dose1_ny_progress_bar)
magtag.graphics.splash.append(dose1_us_progress_bar)
magtag.graphics.splash.append(dose2_ny_progress_bar)
magtag.graphics.splash.append(dose2_us_progress_bar)
response = requests.get(endpoint)

magtag.set_text(f"Population Vaccinated", index=0, auto_refresh=False)

Date = ""

for location in response.json()["vaccination_data"]:
    if location["Location"] == "US" or location["Location"] == "NY":
        Location = location["Location"]

        if Date == "":
            Date = location["Date"]
        elif Date != location["Date"]:
            Date = Date + " & " + location["Date"]

        Administered_Dose1_Pop_Pct = location["Administered_Dose1_Pop_Pct"]
        Administered_Dose2_Pop_Pct = location["Administered_Dose2_Pop_Pct"]

        if location["Location"] == "NY":
            magtag.set_text(
                f"{Location}: {Administered_Dose1_Pop_Pct}%",
                index=1,
                auto_refresh=False,
            )
            dose1_ny_progress_bar.progress = Administered_Dose1_Pop_Pct / 100.0
            dose2_ny_progress_bar.progress = Administered_Dose2_Pop_Pct / 100.0
        elif location["Location"] == "US":
            magtag.set_text(
                f"{Location}: {Administered_Dose1_Pop_Pct}%",
                index=2,
                auto_refresh=False,
            )
            dose1_us_progress_bar.progress = Administered_Dose1_Pop_Pct / 100.0
            dose2_us_progress_bar.progress = Administered_Dose2_Pop_Pct / 100.0

response = requests.get(TIME_URL)
print("-" * 40)
print(response.text)
print("-" * 40)

Date += f" at {response.text}"

magtag.set_text(f"{Date}", index=3, auto_refresh=False)
magtag.refresh()
magtag.exit_and_deep_sleep(12 * 60 * 60)  # Half day
