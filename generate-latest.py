import pathlib
import os
import datetime
import requests
import json
import shutil

API_BASE = "https://api01.viewpointcloud.com/v2/newtonma/"

# TODO: OOP refactor

CONFIG = {"HRA": [None, "HRA-23-{}", 'fullAddress', "historic review"],
          "HDC": [None, "HDC-23-{}", 'fullAddress', "historic district review"],
          "LL": [None, "LL-23-{}", 'fullAddress', "local landmark review"],
          "PR": [None, "PR-23-{}", 'fullAddress', "preservation restriction"],
          "VAR": [None, "VAR-23-{}", 'fullAddress', "variance"],
          "ZBA": [None, "ZBA-23-{}", 'fullAddress', "zoning board of appeals administrative appeal"],
          "SP": [None, "SP-23-{}", 'fullAddress', "special permit"],
          "ZR": [None, "ZR-23-{}", 'fullAddress', "zoning review memo"],
          "ZD": [None, "ZD-23-{}", 'fullAddress', "zoning determination"],
          "RZ": [None, "RZ-23-{}", 'fullAddress', "rezoning"],
          "CR": [None, "CR-23-{}", 'fullAddress', "consistency ruling"],
          "CP": [None, "CP-23-{}", 'fullAddress', "comprehensive permit"],
          "ASPR": [None, "ASPR-23-{}", 'fullAddress', "administrative site plan review"],
          "CONS": [None, "CONS-23-{}", 'fullAddress', "conservation"],
          "FA": [None, "FA-23-{}", 'fullAddress', "fence appeal"],
          "ANR": [None, "ANR-23-{}", 'fullAddress', "ANR plan"],
          "AL": [None, "AL-{}", 'fullAddress', "victualler license"],
          "ALC": [None, "ALC-23-{}", 'fullAddress', "victualler license modification"],
          "FE": [None, "FE-{}", 'fullAddress', "food establishment"],
          "TFE": [None, "TFE-23-{}", 'fullAddress', "temporary food establishment"],
          "TEMP": [None, "TEMP-23-{}", 'fullAddress', "temporary extension of premises"],
          #"OD": [None, "OD-23-{}", 'fullAddress', "one day temporary alcohol"],
          "PMR": [None, "PMR-23-{}", 'locationReportable', "parking meter reservation"],
          "SWB": [None, "SWB-23-{}", None, "sandwich board"],
          "STR": [None, "STR-23-{}", 'fullAddress', "short term rental"],
          "HBOA": [None, "HBOA-23-{}", 'fullAddress', "home business affidavit"],
          "BP": [None, "BP-23-{}", 'fullAddress', "building permit"],
          "BPSO": [None, "BPSO-23-{}", 'fullAddress', "building permit - solar"],
          "BSM": [None, "BSM-23-{}", 'fullAddress', "building permit - sheetmetal"],
          "BCT": [None, "BCT-23-{}", 'fullAddress', "building permit - change of tenant"],
          "BCC": [None, "BCC-23-{}", 'fullAddress', "building permit - change of contractor for an existing building permit"],
          "CO": [None, "CO-23-{}", 'fullAddress', "certificate of occupancy"],
          "ZPA": [None, "ZPA-23-{}", 'fullAddress', "zoning permit"],
          "SR": [None, "SR-23-{}", 'fullAddress', "sign review"],
          "EL": [None, "EL-23-{}", 'fullAddress', "electrical"],
          "ES": [None, "ES-23-{}", 'fullAddress', "electrical - solar"],
          "PL": [None, "PL-23-{}", 'fullAddress', "plumbing"],
          "PIRR": [None, "PIRR-23-{}", 'fullAddress', "plumbing - irrigation"],
          "GF": [None, "GF-23-{}", 'fullAddress', "gas"],
          "FPU": [None, "FPU-23-{}", 'fullAddress', "fire department permit"],
          "ENG": [None, "ENG-23-{}", 'fullAddress', "engineering construction"],
          "CDEP": [None, "CDEP-23-{}", 'fullAddress', "curbing deposit"],
          "VBOX": [None, "VBOX-23-{}", None, "newspaper vending machine"],
          "BWP": [None, "BWP-{}", 'fullAddress', "bodywork practicioner"],
          "RK": [None, "RK-{}", 'fullAddress', "residential kitchen (HHS)"],
          "FWP": [None, "FWP-{}", 'fullAddress', "food permit waiver"],
          "LBR": [None, "LBR-23-{}", None, "leafblower/landscaper registration"],
          "OF": [None, "OF-{}", None, "garbage and offal transport"],
          "RDNA": [None, "RDNA-{}", 'fullAddress', "rDNA facility"],
         }

SORT_DATE = datetime.datetime.now().strftime('%Y-%m-%d')
NICE_DATE = datetime.datetime.now().strftime('%B %d, %Y')

OUTPUT_FILE = 'archive/{0}.html'.format(SORT_DATE)

HTML_DOCUMENT_BEGINNING = "<!DOCTYPE html>\n<html>\n<title>New records for {0}</title>\n<style>\ntable, th, td {{\n  border:1px solid black;\n}}\n</style>\n<body>\n<h1>New records for {0}</h1>(updated daily at 10:00 UTC)<br /><a href='/archive'>View older records</a>\n\n"
HTML_HEADING_AND_TABLE_TEMPLATE = "<h2>New {0} applications</h2>\n\n<table>\n"
HTML_TABLE_ENTRY_TEMPLATE = "<tr><th><a href='https://newtonma.viewpointcloud.com/records/{0}'>{1}</a></th><th>{2}</th></tr>\n"
HTML_TABLE_ENTRY_NONE = "<tr><th>None</th></tr>\n"
HTML_TABLE_END = "</table>\n\n"
HTML_DOCUMENT_END = "<br /><br /><br /><a href=\"https://github.com/jeremyfreudberg/newgov-latest\">Source code</a></body>\n</html>"

def get_record_address(record_number):
  first_result = requests.get(API_BASE + "search_results?criteria=record&key={}".format(record_number)).json()[0]
  first_result_record_number = first_result['resultText'].split()[1].split("(")[0]
  if first_result_record_number != record_number:
    return None
  myrecord_id = first_result['entityID']
  if CONFIG[record_type][2] is None: # yucky scope and bad hack
    fields = requests.get(API_BASE + "form_field_entries?recordID={}".format(myrecord_id)).json()
    applicant = fields["data"][0]["attributes"]["value"]
    return record_number, applicant, myrecord_id
  else:
    location = requests.get(API_BASE + "locations?recordID={}".format(myrecord_id)).json()
    # TODO: latitude and longitude
    address_field = CONFIG[record_type][2] # yucky scope
    address = location['data'][0]['attributes'][address_field]
  return record_number, address, myrecord_id

def get_latest_records(record_type_template, start):
  done = -1 # check one extra record in case not sequential
  num = start
  results = []
  while done < 1:
    res = get_record_address(record_type_template.format(num))
    if res is not None:
      results.append(res)
      num+=1
    else:
      done += 1
  return results, num

f1 = open(pathlib.Path(__file__).with_name('starts.json').absolute(), 'r+')

starts = json.loads(f1.read())

for k in starts.keys():
  CONFIG[k][0] = starts[k]

f2 = open(pathlib.Path(os.path.dirname(os.path.realpath(__file__))).joinpath('archive/{0}.html'.format(SORT_DATE)), 'w')

f2.write(HTML_DOCUMENT_BEGINNING.format(NICE_DATE))

for record_type in CONFIG.keys():
  record_type_template = CONFIG[record_type][1]
  start = CONFIG[record_type][0]
  res = get_latest_records(record_type_template, start)
  starts[record_type] = res[1]
  f2.write(HTML_HEADING_AND_TABLE_TEMPLATE.format(CONFIG[record_type][3]))
  if res[0]:
    for r in res[0]:
      f2.write(HTML_TABLE_ENTRY_TEMPLATE.format(r[2], r[0], r[1]))
  else:
      f2.write(HTML_TABLE_ENTRY_NONE)
  f2.write(HTML_TABLE_END)
  print("Done with "+record_type)

f2.write(HTML_DOCUMENT_END)
f2.truncate()
f2.close()

shutil.copy(OUTPUT_FILE, pathlib.Path(__file__).with_name('index.html').absolute())

f1.seek(0)
f1.write(json.dumps(starts, indent=2))
f1.truncate()
f1.close()
