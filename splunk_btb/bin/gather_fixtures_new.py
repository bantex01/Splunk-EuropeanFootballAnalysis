#!/usr/bin/env python3

import os
import re
import subprocess
import sys
import json
import time
from datetime import date
import requests

from collections import defaultdict

# Globals
today = date.today()
RUN_DIR = os.path.dirname(os.path.join(os.getcwd(), __file__))

divs = ["E0", "E1", "E2", "E3", "EC", "SC0", "SC1", "SC2", "SC3", "D1", "D2", "I1", "I2", "SP1", "SP2", "F1", "F2"]
DIV_DICT = {
    "E0": 1, "E1": 1, "E2": 1, "E3": 1, "EC": 1, "SC0": 1, "SC1": 1, "SC2": 1, "SC3": 1,
    "D1": 1, "D2": 1, "I1": 1, "I2": 1, "SP1": 1, "SP2": 1, "F1": 1, "F2": 1,
    "N1": 1, "B1": 1, "P1": 1, "T1": 1, "G1": 1
}

# Functions

def grab_fixture_csv():
    print("Gathering fixture list")
    date_str = today.strftime("%d/%m/%Y")

    # Remove old lookup files
    try:
        subprocess.check_output("rm -fr /Applications/Splunk/etc/apps/search/lookups/fixtures_*", shell=True, stderr=subprocess.STDOUT)
    except Exception as e:
        print("Problem removing old lookups - " + str(e))

    try:
        subprocess.check_output("rm -fr /Applications/Splunk/footie/fixtures.cs*", shell=True, stderr=subprocess.STDOUT)
    except Exception as e:
        print("Problem removing old fixtures - " + str(e))

    # Download the new fixture file
    try:
        print("Downloading fixtures.csv...")
        response = requests.get("https://www.football-data.co.uk/fixtures.csv")
        if response.status_code == 200 and not response.text.strip().startswith("<HTML>"):
            with open("fixtures.csv", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("Successful gather of fixtures.csv")
        else:
            print("Failed to download valid fixtures.csv (status {}, HTML page?)".format(response.status_code))
            try:
                os.remove("fixtures.csv")
            except Exception as e:
                print("Problem removing dummy fixtures.csv - " + str(e))
    except Exception as e:
        print("Problem gathering fixtures.csv - " + str(e))


def parse_csv_file():
    if not os.path.exists("fixtures.csv"):
        print("No fixtures.csv to parse.")
        return

    with open('fixtures.csv', encoding='utf-8') as f:
        for line in f:
            if "HomeTeam" in line:
                print("Found header line, skipping")
                continue

            split_array = line.strip().split(",")
            if len(split_array) < 5:
                continue

            div_code = split_array[0]
            if div_code in DIV_DICT:
                print("Yes, we're interested in " + str(div_code))
                file_to_write_to = f"/Applications/Splunk/etc/apps/search/lookups/fixtures_{div_code}.csv"

                is_new_file = not os.path.exists(file_to_write_to)
                with open(file_to_write_to, "a", encoding="utf-8") as out_file:
                    if is_new_file and DIV_DICT[div_code] == 1:
                        print("First entry, writing header line")
                        out_file.write("HomeTeam,AwayTeam,GameNumber\n")

                    write_string = f"\"{split_array[3]}\",\"{split_array[4]}\",{DIV_DICT[div_code]}\n"
                    print(write_string.strip())
                    out_file.write(write_string)
                    DIV_DICT[div_code] += 1


# Main
grab_fixture_csv()
parse_csv_file()

