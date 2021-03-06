"""
    Bell scheduler for PacPoint
    Author: Michael Wallar (michael@wallar.net)

    This module is responsible for handling the bell schedule for PacPoint schools.
    The main behavior and schedule is defined in a json file, passed as the first
    parameter to this program. The json document should be stylized as the following:
    {
        "calendar": {
            "default": {
                "Monday": "normal_day",
                "Tuesday": "normal_day",
                "Wednesday": "normal_day",
                "Thursday": "normal_day",
                "Friday": "normal_day"
            },
            "2017-08-17": "half_day"
        },
        "schedules": {
            "normal_day": {
                "08:00": "high_school",
                "08:20": "junior_high"
            },
            "half_day": {
                "09:00": "high_school",
                "09:20": "junior_high",
                "00:56": "test_thing"
            }
        },
        "patterns": {
            "high_school": {
                "rings": 1,
                "duration": 2,
                "spacing": 1
            },
            "junior_high": {
                "rings": 3,
                "duration": 1,
                "spacing": 1
            },
            "test_thing": {}
        }
    }

    The above json will tell the system that Wednesdays are half days, and give the
    specific times for the different types of bells.

    This module uses the schedule module (https://pypi.python.org/pypi/schedule) by
    Daniel Bader.

    This module is licensed under MIT. See license.txt for more information.
"""
#!/usr/bin/python

# Disable pylint's aggressive definition of constants.
# pylint: disable=C0103

# Disable pylint's dislike of globals.
# pylint: disable=W0603

# Disable pylint's dislike of lines > 100 characters.
# pylint: disable=C0301

# Python 3.x future-proofing.
from __future__ import print_function

import time
import datetime
import sys
import json
import logging

pinlessMode = False
if not pinlessMode:
    try:
        import RPi.GPIO as GPIO
    except ImportError:
        print("Could not load RPi.GPIO. Is this installed on a valid device? Defaulting to pinless mode.")
        pinlessMode = True

# Configure Pi pin output.
bellPins = [7, 11, 13]
if not pinlessMode:
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(True)
    for pin in bellPins:
        GPIO.setup(pin, GPIO.OUT)

# Establish logging.
logging.basicConfig(filename="bellSchedule.log", filemode="w", format="%(asctime)s %(message)s", level=logging.DEBUG)

# Make sure we have the third party schedule module installed.
try:
    import schedule
except ImportError:
    logging.error("Could not find schedule module. Install the module using:")
    logging.error("    pip install schedule")
    sys.exit(0)

jsonFile = None
jsonConfig = None
curSchedule = None

def power_bells(state):
    """Powers or unpowers the bells."""
    if not pinlessMode:
        if state:
            for pin in bellPins:
                GPIO.output(pin, GPIO.HIGH)
        elif not state:
            for pin in bellPins:
                GPIO.output(pin, GPIO.LOW)
    else:
        logging.debug("Bell state: " + str(state))

def ring_bells():
    """Rings the school bells in a pattern for the given schedule/time."""
    # Need to get the pattern for this time slot and apply it.
    curTime = time.strftime("%H:%M")
    if curTime not in jsonConfig["schedules"][curSchedule]:
        logging.error("Couldn't find time record for time " + curTime + " in schedule " + curSchedule)
        return

    # Obtain the pattern to use.
    pattern = jsonConfig["schedules"][curSchedule][curTime]
    if pattern not in jsonConfig["patterns"]:
        logging.error("Could not find pattern '" + pattern + "'.")
        return

    # Play the pattern.
    logging.debug("Playing bell: " + pattern)
    bellRings = jsonConfig["patterns"][pattern]["rings"]
    bellDuration = jsonConfig["patterns"][pattern]["duration"]
    bellSpacing = jsonConfig["patterns"][pattern]["spacing"]
    for _ in range(bellRings):
        power_bells(True)
        time.sleep(bellDuration)
        power_bells(False)
        time.sleep(bellSpacing)

def reload_schedule():
    """Reloads the schedule from our json file."""
    global jsonConfig
    global curSchedule

    jsonConfig = None
    curSchedule = None

    # Clear currently scheduled bells.
    schedule.clear("current")

    logging.debug("Reloading schedule...")
    with open(jsonFile) as jsonFileHandle:
        jsonConfig = json.load(jsonFileHandle)

    # Check that default structure for json config is respected.
    if "calendar" not in jsonConfig or "default" not in jsonConfig["calendar"]:
        logging.error("Malformed json config. Invalid calendar table.")
        return
    elif "schedules" not in jsonConfig:
        logging.error("Malformed json config. Invalid schedules table.")
        return
    elif "patterns" not in jsonConfig:
        logging.error("Malformed json config. Invalid patterns table.")
        return

    # Check to see if this date has a specific schedule.
    curDate = datetime.datetime.today().strftime("%Y-%m-%d")
    if curDate in jsonConfig["calendar"]:
        curSchedule = jsonConfig["calendar"][curDate]
    else:
        # If this isn't a special day, we look up the schedule by day of the week.
        curDayOfWeek = datetime.datetime.now().strftime("%A")
        if curDayOfWeek in jsonConfig["calendar"]["default"]:
            curSchedule = jsonConfig["calendar"]["default"][curDayOfWeek]
        else:
            logging.debug("No schedule found for date.")
            return

    # Now that we have the schedule to use, does it exist?
    if curSchedule not in jsonConfig["schedules"]:
        logging.error("Schedule" + curSchedule + " not found in json config. Aborting.")
        return

    # Add bells for this schedule.
    for bellTime in jsonConfig["schedules"][curSchedule]:
        schedule.every().day.at(bellTime).do(ring_bells).tag("current")
        logging.debug("Scheduled bells using pattern '" + jsonConfig["schedules"][curSchedule][bellTime] + "' at " + bellTime)

# Make sure our first argument is a file.
if len(sys.argv) != 2:
    logging.error("Invalid use. Usage:")
    logging.error("    sudo python " + sys.argv[0] + " <path to json config>")
    sys.exit(0)
jsonFile = sys.argv[1]

# Main execution
try:
    logging.debug("System online.")

    # Initial calls.
    reload_schedule()

    # At 2am, we want to reload the schedule from our json dataset.
    schedule.every().day.at("02:00").do(reload_schedule)

    while True:
        schedule.run_pending()
        time.sleep(1)
except KeyboardInterrupt:
    logging.debug("Execution manually broken.")
finally:
    if not pinlessMode:
        GPIO.cleanup()
