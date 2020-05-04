#!/usr/bin/python


import os
import filecmp
import re
import subprocess
import sys
import json
import time
import ntpath
from datetime import date
today = date.today()

from collections import defaultdict

# Globals
RUN_DIR = os.path.dirname(os.path.join(os.getcwd(), __file__))

divs = ["E0","E1","E2","E3","EC","SC0","SC1","SC2","SC3","D1","D2","I1","I2","SP1","SP2","F1","F2"]
DIV_DICT = {
		"E0":1,
		"E1":1,
		"E2":1,
                "E3":1,
                "EC":1,
                "SC0":1,
                "SC1":1,
                "SC2":1,
                "SC3":1,
                "D1":1,
                "D2":1,
                "I1":1,
                "I2":1,
                "SP1":1,
                "SP2":1,
		"F1":1,
		"F2":1,
		"N1":1,
		"B1":1,
		"P1":1,
		"T1":1,
		"G1":1
}

# Functions

def grab_fixture_csv():

	print "gathering fixture list"
	date = today.strftime("%d/%m/%Y")

	# let's clear up any previous lookups and fixtures.csv

	rm_lookup_cmd = "rm -fr /opt/splunk/etc/apps/splunk_btb/lookups/fixtures_*"
	try:
		out = subprocess.check_output([rm_lookup_cmd], shell=True, stderr=subprocess.STDOUT)
	except Exception, e:
		print "problem removing old lookups - " +str(e)

        rm_old_fixtures = "rm -fr /opt/splunk/etc/apps/splunk_btb/bin/fixtures.cs*"
        try:
                out = subprocess.check_output([rm_old_fixtures], shell=True, stderr=subprocess.STDOUT)
        except Exception, e:
                print "problem removing old lookups - " +str(e)


	try:
		wget_cmd = "wget https://www.football-data.co.uk/fixtures.csv"
		out = subprocess.check_output([wget_cmd], shell=True, stderr=subprocess.STDOUT)
		print out

		if ("200 OK") not in out:
			print "fixtures.csv not found, removing dummy file"
			try:
				rm_cmd = "rm -fr fixtures.csv"
				out = subprocess.check_output([rm_cmd], shell=True, stderr=subprocess.STDOUT)
			except Exception, e:
				print "problem removing fixtures.csv"

		else:
			print "Successful gather of fixtures.csv"


	except Exception, e:
		print "problem gathering fixtures.csv" + str(e)


def parse_csv_file():

	with open('fixtures.csv') as f:
		for line in f:
			if "HomeTeam" in line:
				print "found header line, skipping"
				continue
			else:
				split_array = line.split(",")
				print split_array[0]	
				# let's check we're interested in the league
				if split_array[0] in DIV_DICT:
					print "yes, we're interested in "+str(split_array[0])
					file_to_write_to = "/opt/splunk/etc/apps/splunk_btb/lookups/fixtures_" +str(split_array[0]) +".csv"	
					f = open(file_to_write_to,"a")
					if DIV_DICT[split_array[0]] == 1:
						print "first entry, let's put header line in"
						f.write("HomeTeam,AwayTeam,GameNumber\n")

					write_string = "\"" +split_array[3] +"\"" + "," + "\"" +split_array[4] + "\"" + "," + str(DIV_DICT[split_array[0]]) + "\n"
					print str(write_string)
					f.write(write_string)	
					DIV_DICT[split_array[0]] = DIV_DICT[split_array[0]] + 1						



# Main

# Grab fixtures list
grab_fixture_csv()
parse_csv_file()


