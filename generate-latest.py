import requests
import json

API_BASE = "https://api01.viewpointcloud.com/v2/newtonma/"

CONFIG = {"HRA": [None, "HRA-22-{}", 'fullAddress', "historic review"],
          "HDC": [None, "HDC-22-{}", 'fullAddress', "historic district review"],
          "LL": [None, "LL-22-{}", 'fullAddress', "local landmark review"],
          "VAR": [None, "VAR-22-{}", 'fullAddress', "variance"],
          "ZBA": [None, "ZBA-22-{}", 'fullAddress', "zoning board appeal"],
          "SP": [None, "SP-22-{}", 'fullAddress', "special permit"],
          "ZR": [None, "ZR-22-{}", 'fullAddress', "zoning review memo"],
          "ZD": [None, "ZD-22-{}", 'fullAddress', "zoning determination"],
          "RZ": [None, "RZ-22-{}", 'fullAddress', "rezoning"],
          "CR": [None, "CR-22-{}", 'fullAddress', "consistency ruling"],
          "CP": [None, "CP-22-{}", 'fullAddress', "comprehensive permit"],
          "ASPR": [None, "ASPR-22-{}", 'fullAddress', "administrative site plan review"],
          "CONS": [None, "CONS-22-{}", 'fullAddress', "conservation"],
          "ZPA": [None, "ZPA-22-{}", 'fullAddress', "zoning permit"],
          "FA": [None, "FA-22-{}", 'fullAddress', "fence appeal"],
          "ANR": [None, "ANR-22-{}", 'fullAddress', "ANR plan"],
          "AL": [None, "AL-{}", 'fullAddress', "victualler"],
          "FE": [None, "FE-{}", 'fullAddress', "food establishment"],
          "PMR": [None, "PMR-22-{}", 'locationReportable', "parking meter reservation"],
         }
# happy new year :(

HTML_DOCUMENT_BEGINNING = "<!DOCTYPE html>\n<html>\n<title>New records</title>\n<style>\ntable, th, td {\n  border:1px solid black;\n}\n</style>\n<body>\n<h1>New records (updated daily at 10:00 UTC)</h1>\n\n"
HTML_HEADING_AND_TABLE_TEMPLATE = "<h2>New {0} applications</h2>\n\n<table>\n"
HTML_TABLE_ENTRY_TEMPLATE = "<tr><th>{0}</th><th>{1}</th></tr>\n"
HTML_TABLE_ENTRY_NONE = "<tr><th>None</th></tr>\n"
HTML_TABLE_END = "</table>\n\n"
HTML_DOCUMENT_END = "<br /><br /><br /><a href=\"https://github.com/jeremyfreudberg/newgov-latest\">Source code</a></body>\n</html>"

def get_record_address(record_number):
  first_result = requests.get(API_BASE + "search_results?criteria=record&key={}".format(record_number)).json()[0]
  first_result_record_number = first_result['resultText'].split()[1].split("(")[0]
  if first_result_record_number != record_number:
    return None
  myrecord_id = first_result['entityID']
  location = requests.get(API_BASE + "locations?recordID={}".format(myrecord_id)).json()
  address_field = CONFIG[record_type][2] # yucky scope
  address = location['data'][0]['attributes'][address_field]
  return record_number, address

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

f1 = open('starts.json', 'r+')

starts = json.loads(f1.read())

for k in starts.keys():
  CONFIG[k][0] = starts[k]

f2 = open('index.html', 'w')

f2.write(HTML_DOCUMENT_BEGINNING)

for record_type in CONFIG.keys():
  record_type_template = CONFIG[record_type][1]
  start = CONFIG[record_type][0]
  res = get_latest_records(record_type_template, start)
  starts[record_type] = res[1] - 1
  f2.write(HTML_HEADING_AND_TABLE_TEMPLATE.format(CONFIG[record_type][3]))
  if res[0]:
    for r in res[0][-1:0:-1]:
      f2.write(HTML_TABLE_ENTRY_TEMPLATE.format(r[0], r[1]))
    f2.write(HTML_TABLE_ENTRY_TEMPLATE.format(res[0][0][0] + " (old)", res[0][0][1]))
  else:
      f2.write(HTML_TABLE_ENTRY_NONE)
  f2.write(HTML_TABLE_END)

f2.write(HTML_DOCUMENT_END)
f2.truncate()
f2.close()

f1.seek(0)
f1.write(json.dumps(starts, indent=2))
f1.truncate()
f1.close()
