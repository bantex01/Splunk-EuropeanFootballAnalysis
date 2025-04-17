#!/usr/bin/env python3

import os
import re
import subprocess
import sys
import json
import time
from collections import defaultdict

# Globals
RUN_DIR = os.path.dirname(os.path.join(os.getcwd(), __file__))
CSV_DIR = os.path.join(RUN_DIR, "csv")
sources = []

# Functions

def parse_data_source():
    conf_file_path = "data_sources.dat"
    if not os.path.exists(conf_file_path):
        print("File does not exist")
        sys.exit(2)

    with open(conf_file_path, 'r') as conf_file:
        for conf_line in conf_file:
            if re.match(r'^#', conf_line) or re.match(r'^\s', conf_line):
                continue
            sources.append(conf_line.strip())

def clear_splunk_index():
    try:
        curl_cmd = (
            "/usr/bin/curl -m 10 -k -s -u admin:some_passwd "
            "-d \"search=search index=football_24_25 earliest_time=1 latest_time=\\\"08/31/2030:20:00:00\\\" | delete\" "
            "-d output_mode=json https://localhost:8089/services/search/jobs"
        )
        out = subprocess.check_output(curl_cmd, shell=True, stderr=subprocess.STDOUT).decode('utf-8')
        sid_dict = json.loads(out)
        sid = sid_dict['sid']

        time.sleep(5)

        try:
            status_cmd = (
                f"/usr/bin/curl -m 10 -k -s -u admin:some_passwd "
                f"https://localhost:8089/services/search/jobs/{sid}"
            )
            out = subprocess.check_output(status_cmd, shell=True, stderr=subprocess.STDOUT).decode('utf-8')
            for line in out.splitlines():
                if re.search(r'dispatchState">\w+<', line):
                    dispatch_state = re.search(r'dispatchState">(\w+)<', line).group(1)
                    break

            if dispatch_state == "DONE":
                print("Search seems to have gone through")
            else:
                print("Check index, something went wrong")
                sys.exit(2)

        except Exception as e:
            print("Exception caught checking status of search job:", str(e))

    except Exception as e:
        print("Exception caught submitting deletion search:", str(e))

import requests

def grab_and_ingest_csv_files():
    for csv_url in sources:
        print(f"Gathering {csv_url}")
        try:
            response = requests.get(csv_url)
            if response.status_code != 200:
                print(f"{csv_url} not found (HTTP {response.status_code}), skipping.")
                continue

            if response.text.strip().startswith("<HTML>"):
                print(f"Received HTML instead of CSV for {csv_url}. Skipping.")
                continue

            csv_file = os.path.basename(csv_url)
            print(csv_file)

            with open(csv_file, 'w', encoding='utf-8') as f:
                f.write(response.text)

            if csv_file == "EC.csv":
                print("Found conference file, converting encoding")
                with open("EC.csv", 'r', encoding='cp1252') as inp, open("EC.csv.temp", 'w', encoding='utf-8') as outp:
                    for line in inp:
                        outp.write(line)
                os.replace("EC.csv.temp", "EC.csv")

            # Replace characters like sed did
            with open(csv_file, 'r', encoding='utf-8') as inp, open(csv_file + ".1", 'w', encoding='utf-8') as outp:
                for line in inp:
                    outp.write(line.replace(">", "gt").replace("<", "lt"))

            if os.path.exists(csv_file + ".1"):
                os.remove(csv_file)
                os.rename(csv_file + ".1", csv_file)
                print(f"Cleaned {csv_file} and ready to ingest")
            else:
                print("Something went wrong with character replacement")
                exit(2)

            # Ingest into Splunk
            oneshot_cmd = f"/Applications/Splunk/bin/splunk add oneshot {csv_file} -sourcetype footie_csv -index football_24_25 -auth admin:some_passwd"
            time.sleep(5)
            try:
                output = subprocess.check_output(oneshot_cmd, shell=True, stderr=subprocess.STDOUT).decode('utf-8')
                if "added" in output:
                    print(f"{csv_file} added successfully, removing file")
                    os.remove(csv_file)
                else:
                    print(f"Could not confirm ingestion success:\n{output}")
            except Exception as e:
                print(f"Problem ingesting {csv_file}, exception: {e}")
                continue

        except Exception as e:
            print(f"Problem gathering {csv_url}, exception: {e}")


# Main
if __name__ == "__main__":
    print("Parsing sources file to ascertain csv list...")
    parse_data_source()
    print("Clearing Splunk index, ready for new ingest...")
    clear_splunk_index()
    print("Grabbing new CSV files...")
    grab_and_ingest_csv_files()

