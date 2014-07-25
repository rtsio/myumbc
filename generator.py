import argparse
import re
import base64
import time
from subprocess import call
from pytagcloud.lang.counter import get_tag_counts
from myumbc import Database
from ConfigParser import SafeConfigParser, RawConfigParser

def build_apiurl(counts):

	max_scale = counts[0][1] + 10
	base_url = "http://chart.apis.google.com/chart?"
	first_option_string = "chf=bg,s,FFCC33"
	labels = "chxl=1:|"    
	second_option_string = "chxr=0,0," + str(max_scale) + "&chxt=x,y&chbh=r,1,6&chs=256x400&cht=bhs&chco=666666,C6D9FD&chds=0," + str(max_scale)
	values = "chd=t1:"
	third_option_string = "chma=20,20,20,30"
	
	labels_reverser = []
	for i, (word, count) in enumerate(counts[:10]):
		labels_reverser.append(word)
		values += (str(count) + ',')
	for i in reversed(labels_reverser):
		labels += (i + '|')
			
	return ('&'.join([base_url,first_option_string,labels[:-1],second_option_string,values[:-1],third_option_string]))

config = SafeConfigParser()
config.read('config.txt')

myumbc_user = config.get('myumbc', 'username')
myumbc_pw = base64.b64decode(config.get('myumbc', 'password'))
database_host = config.get('database', 'host')
database_user = config.get('database', 'username')
database_pw = base64.b64decode(config.get('database', 'password'))
database_name = 'myumbc6000'

db = Database(database_host, database_user, database_pw, database_name)
parser = argparse.ArgumentParser(description="Generate common word charts for myUMBC users.")
parser.add_argument('date', help="Date from last scrape (to check if chart needs generating)")
args = parser.parse_args()

avatar_path = "/home/ross/myumbc/avatars/"

first_user = 1
last_user = db.last_user() + 1
blacklist = [0]
# %group/%/medium%"
group_avatar_blacklist = [5738, 4311, 6913, 5789, 4918, 6776, 6826, 6766, 5122, 5130, 6606, 5969, 5448, 4744, 7103, 5284, 6527, 6133, 5858, 6482, 6932, 5911, 6703, 5200, 5258, 6843, 7177, 5139, 7222, 6561, 7457, 5160, 7481, 5216, 7045, 7055, 7059, 5287, 6828, 5294, 5053, 6082, 6855, 5230, 6867, 5354, 5370, 5628]

for x in xrange(first_user, last_user):
	
	if x not in blacklist:
		user_query = db.need_update(x, args.date)
		if user_query:
			filename = avatar_path + str(x) + '.png'
			avatar_url = (re.search(r'(.*)\/', user_query).group(0)) + "xxxlarge.png"
			if x not in group_avatar_blacklist:
				call(["wget", "-O", filename, avatar_url])
				time.sleep(1)
			posts = db.get_posts(x)
			counts = get_tag_counts(posts)    
			if (len(counts)) > 10:
				download_string = build_apiurl(counts)
				try:
					download_string.decode('ascii')
				except UnicodeEncodeError:
					print "User " + str(x) + " had malformed characters - labels are printed below"
					print "User " + str(x) + ": "
					print counts
				else:				
					db.insert_chart(x, download_string)
db.close()
