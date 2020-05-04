#!/usr/bin/python


import os
import filecmp
import re
import subprocess
import sys
import json
import time
import ntpath

from collections import defaultdict

# Globals
RUN_DIR = os.path.dirname(os.path.join(os.getcwd(), __file__))
CSV_DIR = RUN_DIR + "/csv"

global sources
sources = []
# Functions

def parse_data_source():

	conf_file = "data_sources.dat"
	if (os.path.exists(conf_file)):
		conf_file = open(conf_file,'r')
		for conf_line in conf_file:
			#print "conf line is "+conf_line
			if (re.match(r'^#',conf_line) or re.match(r'^\s',conf_line)):
				continue

			else:
				sources.append(conf_line.rstrip())

	else:
		print "File does not exist"
		exit(2)


def clear_splunk_index():

	try:
		curl_cmd = "/usr/bin/curl -m 10 -k -s -u admin:goober13 -d \"search=search index=football_19_20 earliest_time=1 latest_time=\"08/31/2030:20:00:00\" | delete\" -d output_mode=json https://localhost:8089/services/search/jobs"

		out = subprocess.check_output([curl_cmd], shell=True, stderr=subprocess.STDOUT)
		sid_dict = json.loads(out)
		sid = sid_dict['sid']

		time.sleep(5)

		try:
			curl_cmd = "/usr/bin/curl -m 10 -k -s -u admin:goober13 https://localhost:8089/services/search/jobs/" + sid
			out = subprocess.check_output([curl_cmd], shell=True, stderr=subprocess.STDOUT)
			for line in out.splitlines():
				if (re.match(r'.*dispatchState\">\w+<.*', line)):
					dispatchState = re.search(r'.*dispatchState\">(\w+)<.*', line).group(1)
					break

			if (dispatchState == "DONE"):
				print "Search seems to have gone through"
			else:
				print "Check index, something went wrong"
				exit(2)

		except Exception, e:
			print "exception caught checking status of search job "+str(e)

	except Exception, e:
		print "exception caught submiting deletion search "+str(e)


def grab_and_ingest_csv_files():

	for csv in sources:
		print "gathering "+csv
		try:
			wget_cmd = "wget "+csv
			out = subprocess.check_output([wget_cmd], shell=True, stderr=subprocess.STDOUT)
			#print out
			csv_file = os.path.basename(csv)
			print csv_file

			if ("200 OK") not in out:
				print csv + " not found, removing dummy file"
				try:
					rm_cmd = "rm -fr "+str(csv_file)
					out = subprocess.check_output([rm_cmd], shell=True, stderr=subprocess.STDOUT)
				except Exception, e:
					print "problem removing "+str(csv)

			else:
				sed_cmd = "cat " + csv_file + " | sed 's/>/gt/g' | sed 's/</lt/g' > " + csv_file + ".1" 
				print sed_cmd
				print "Successful gather of "+str(csv_file)

				sed_run = subprocess.check_output([sed_cmd], shell=True, stderr=subprocess.STDOUT)
				if (os.path.exists(csv_file + ".1")):
					print "amended file exists"
					os.remove(csv_file)
					os.rename(csv_file +".1",csv_file)	
				else:
					print "something went wrong with the sed efforts"
					exit(2)

				oneshot_cmd = "/opt/splunk/bin/splunk add oneshot " +str(csv_file) + " -sourcetype footie_csv -index football_19_20 -auth admin:goober13"
				time.sleep(5)
				try:
					out = subprocess.check_output([oneshot_cmd], shell=True, stderr=subprocess.STDOUT)
					if "added" in out:
						print str(csv_file) + " added successfully, removing file"
						rm_cmd = "rm -fr "+str(csv_file)
						out = subprocess.check_output([rm_cmd], shell=True, stderr=subprocess.STDOUT)
				except Exception, e:
					print "problem ingesting " +str(csv) + " review output, aborting"
					exit(2)

		except Exception, e:
			print "problem gathering "+csv + " exception is "+str(e)



# Main
print "Parsing sources file to ascertain csv list..."
parse_data_source()
print "clearing splunk index, ready for new ingest..."
clear_splunk_index()
print "Grabbing new CSV files..."
grab_and_ingest_csv_files()
