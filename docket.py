#! python 3
# docket.py - preps docket for given day
# Things to Add:
# 
# Determine jury demand
# List witnesses
# List whether DV case, for trials who Ws are


import requests, sys, time, datetime, bs4, subprocess, re
from tqdm import tqdm
def now_milliseconds():
	return int(time.time() * 1000)

# THEMIS VARIABLES
# The URL for the authentication page for main website
url = 'http://denvercourt.dcc.dnvr/courtnet/login.aspx'
# The URL for the get request to search a name
get_url = 'http://denvercourt.dcc.dnvr/courtnet/DCCDockets.aspx?'
# The URL for the get request to search a case
casesearch_url = 'http://denvercourt.dcc.dnvr/courtnet/court_result.aspx?caseNo='

# payload info generated from dev tools, Network tab after submitting request
# was able to find form data in the head tab and used that directly
payload = {'__LASTFOCUS':'',
	   '__EVENTTARGET':'',
	   '__EVENTARGUMENT':'',
	   '__VIEWSTATE':'/wEPDwUJNjQyODUzNDYyD2QWAmYPZBYCAgMPZBYCAgUPZBYCAgUPD2QWAh4Fc3R5bGUFGXRleHQtdHJhbnNmb3JtOnVwcGVyY2FzZTtkGAEFHl9fQ29udHJvbHNSZXF1aXJlUG9zdEJhY2tLZXlfXxYBBSJjdGwwMCRDb250ZW50UGxhY2VIb2xkZXIxJGNiX0FncmVlWbd1tFkrgCyhC18H9VpiFgelE+k=', 
	   '__VIEWSTATEGENERATOR':'355B8235',
	   '__EVENTVALIDATION':'/wEWBQK90dzODALJ4fq4BwL90KKTCALC4Iy6CgK8haTMDE41xwE2XedmDLm1WF64yqlP/gCC',
	   'ctl00$ContentPlaceHolder1$txtUserName':'XXXX',
	   'ctl00$ContentPlaceHolder1$txtPassword':'XXXXX',
	   'ctl00$ContentPlaceHolder1$cb_Agree':'on',
	   'ctl00$ContentPlaceHolder1$cmdEnter':'Enter'}


############# ENTRY POINT FOR CODE #########################
f = open("C:\\Users\\XXXXX\\Downloads\\temp.txt", 'w')


with requests.Session() as s:
	p = s.post(url, data=payload)
	p2 = s.get(get_url + "d=" + "08/14/2017" + '&k=original&_' + str(now_milliseconds()) + '&r=3H')

	# regex over CSS selectors because THEMIS returns a Word document for a docket search, which is the worst for a CSS search
	list_caseNos = re.findall(">[0-9][0-9]G[SV][0-9][0-9][0-9][0-9][0-9][0-9]<", p2.text)
	# strip unwanted chars
	for caseno_string_index in range(len(list_caseNos)):	
		list_caseNos[caseno_string_index] = list_caseNos[caseno_string_index].strip('<>')
	f.write(str(len(list_caseNos)) + " cases on docket")
	for caseNo in tqdm(list_caseNos): # tqdm is progress bar
		# Case Number
		f.write('\n' + caseNo)
		p3 = s.get(casesearch_url + caseNo + '&_' + str(now_milliseconds()))
		searchHTML = bs4.BeautifulSoup(p3.text, "html.parser")
		list_party = searchHTML.select('#p_gen_party_intra td')
		list_offenses = searchHTML.select('#p_gen_offense td')
		list_bondinfo = searchHTML.select('#p_gen_bond td')
		list_bondamount = searchHTML.select('#p_gen_bondamount td')
		list_actions = searchHTML.select('#p_gen_actions td')
		list_minutes = searchHTML.select('#p_gen_actions td[colspan^="10"]')
		str_Custody_Status = ""
		if "BOND" not in list_party[6].getText().strip():
			str_Custody_Status = "IN CUSTODY or BOND RELEASED"
		else:
			str_Custody_Status = list_party[6].getText().strip()
		str_Defense_Counsel = "\t\t\t\t"
		if list_party[30].getText().strip():
			str_Defense_Counsel = list_party[30].getText().strip().lower()
		
		# Name
		f.write("\t\t" + list_party[1].getText().strip() + ", " + list_party[2].getText().strip())		
		# Hearing Type
		str_hearing_type = ""
		if "08/14/2017" in list_actions[0].getText():
			str_hearing_type = "\t\t" + list_actions[1].getText().strip() + '\n'
		else:
			if "TRIAL" in list_actions[1].getText():
				str_hearing_type = "\t" + list_actions[7].getText().strip() + " & SFT on " + list_actions[0].getText().strip()[:11] + '\n'
			else:
				str_hearing_type = "\t" + list_actions[7].getText().strip() + '\n'
		f.write(str_hearing_type)
		# Facts, Charges
		f.write("Facts: ")
		for k in range(len(list_offenses)):
			if (k + 5) % 5 == 0:
				f.write("\t\t\t\t\t" + list_offenses[k].getText().strip() + " " + list_offenses[k + 1].getText().strip().lower() + '\n')

		# Custody Status, Appearance Info, and Speedy

		str_ST_Date = ""
		for j in range(len(list_actions)):
			if "SPEEDY TRIAL STARTS" in list_actions[j].getText() or "SPEEDY TRIAL WAIVED" in list_actions[j].getText():
				str_ST_Date = list_actions[j - 1].getText().strip()[:11]
				break
		f.write("\nSS   " + "AB   " + "LKA   " + "SchedSh   " + "211   " + "M4DJ   " + "Other   \t" + str_Custody_Status + '\n')
		
		# Counsel, Bond Amount/Info, Minutes
		str_bondinfo = "no bond info"
		for l in range(len(list_bondinfo)):
			if "POSTED" in list_bondinfo[l].getText():
				str_bondinfo = list_bondinfo[l + 1].getText().strip() + " posted on " + list_bondinfo[l - 1].getText().strip()[:11]
			elif "NO" in list_bondinfo[l].getText():
				str_bondinfo = "PR granted on: " + list_bondinfo[l - 1].getText().strip()[:11] + " unsecured " + list_bondinfo[l - 2].getText().strip()
		str_bondamount = ""
		str_bondsetdate = ""
		if len(list_bondamount) > 0:
			str_bondamount = list_bondamount[0].getText().strip()
			str_bondsetdate = list_bondamount[1].getText().strip()
		str_minutes = "Minutes from last hearing: "
		if len(list_minutes) > 0:
			str_temp = list_minutes[0].getText().strip()[9:].strip().replace("  ", "").replace("\n", "").replace("\r", "")
			str_minutes = str_minutes + str_temp

		# Speedy and Bond
		f.write("ST: " + str_ST_Date + "\t\t\t\t\t" + str_bondinfo + '\n')


		f.write("Counsel: " + str_Defense_Counsel + "\tBond: " + str_bondamount + " set on " + str_bondsetdate + '\n')
		str_FTAs = ""
		for j in range(len(list_actions)):
			if "FTA" in list_actions[j].getText() and "JUDGE" not in list_actions[j].getText():
				f.write(" -- FTAd on " + list_actions[j - 4].getText().strip()[:11]) # D's CAN have multiple FTAs for one case
		f.write(str_minutes)

		# Probation and Sentencing; Line
		if "REVIEW DATE" in str_hearing_type or "REVOCATION" in str_hearing_type or "SHOW CAUSE" in str_hearing_type:
			list_sentence = searchHTML.select('#p_gen_sentence td')
			f.write("\nSentence:\n")
			for r in range(len(list_sentence)):
				f.write(list_sentence[r].getText().strip().lower() + " ")
				if (r+1) % 6 == 0:
					f.write('\n')
		f.write("\n_____________________________________________________________________________________\n")
		time.sleep(2.0) # BE POLITE TO SCRAPED SERVER

f.close()
subprocess.call(['C:\\windows\\system32\\notepad.exe', 'C:\\Users\\XXXXX\\Downloads\\temp.txt'])
