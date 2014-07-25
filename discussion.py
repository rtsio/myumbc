#!/usr/bin/python
import argparse
import time
import re
import sys
import base64
from ConfigParser import SafeConfigParser, RawConfigParser
from bs4 import BeautifulSoup
from myumbc import Scraper, Database

def progress(x, current, limit):
    print "Discussion: " + str(x) + "\t" + str((float(current)/limit) * 100) + "%",

# Read config files
# If you get a missing section error, you must run this script from the directory
# with the config file, as python determines paths from the point of execution
config = SafeConfigParser()
config.read('config.txt')

myumbc_user = config.get('myumbc', 'username')
myumbc_pw = base64.b64decode(config.get('myumbc', 'password'))
database_host = config.get('database', 'host')
database_user = config.get('database', 'username')
database_pw = base64.b64decode(config.get('database', 'password'))
database_name = config.get('database', 'database')

scraper = Scraper()
db = Database(database_host, database_user, database_pw, database_name)
scraper.login(myumbc_user, myumbc_pw)

# Read in blacklists - ignored threads/comments
blacklist = open('discussion_blacklist.txt', 'a+')
blacklisted_threads = blacklist.read().splitlines()
blacklisted_comments = []

arguments = argparse.ArgumentParser()
arguments.add_argument('-start', action='store', type=int, required=True)
arguments.add_argument('-end', action='store', type=int, required=True)
arguments.add_argument('-date', action='store', required=True)
args = arguments.parse_args()

start = args.start
end = args.end + 1
total = end - start
date = args.date

for x in xrange(start, end):

    page_exists = False
    current_discussion = str(x)
    if current_discussion not in blacklisted_threads:
        if scraper.valid("discussions", current_discussion):
	    page_exists = True
        else:
            blacklist.write(current_discussion + '\n')
    
    if (page_exists):
       
        soup = BeautifulSoup(scraper.gethtml())
        author_tag = soup.find(class_="discussion-post")
        author_post_id = x + 1000000
        
        author_name = author_tag.find(class_="user first").string
        author_paws = int(author_tag.find(class_="count first last").string)
        author_avatar = re.search(r'background-image: url\(\'(.*)\?', author_tag.find(class_=re.compile("avatar"))['style']).group(1)
        
        author_inner_content = author_tag.find(class_="html-content").find(class_="html-content")
        if not author_inner_content:
            author_inner_content = author_tag.find(class_="button first last")
        else:
            for tag in author_inner_content.find_all('embed'):
                embed_link = tag['src']
                tag.replace_with("(Embed object pointing to " + embed_link + " removed from original post)")
            for tag in author_inner_content.find_all('iframe'):
                iframe_link = tag['src']
                tag.replace_with("(Iframe object pointing to " + iframe_link + " removed from original post)")
            for tag in author_inner_content.find_all('object'):
                tag.replace_with("(Object tag removed from original post)")
            for tag in author_inner_content.find_all('param'):
                tag.replace_with("(Param tag removed from original post)")

        content_title = u'<b>(This post is a discussion topic originally entitled ' + author_tag.find(class_="title").string + ')</b> <br>'
        content = content_title + unicode(author_inner_content)
        
        content = re.sub(r'<span.*?>|<\/span>', '', content)
        content = re.sub(r'\sclass=".*?"', '', content)

        if not db.post_exists(author_post_id):
            db.process_post(author_post_id, x, author_name, author_paws, author_avatar, date, content, "d")
        else:
            db.update_post(author_post_id, x, author_name, author_paws, date, content, "d")

        for tag in soup.find_all(class_=re.compile("comment-\d+")):
            comment_id = tag['data-comment-id']
            comment_name = tag.find(class_="poster").string
            if (tag['class'][3] != 'mine'):
                if tag['class'][3] != 'removed':
                    comment_paws = int(tag.find(class_="paw").find(class_="count").string)
                    comment_avatar = re.search(r'background-image: url\(\'(.*)\?', tag.find(class_="avatar small")['style']).group(1) 
                    comment_inner_content = tag.find(class_="html-content")
                    if comment_inner_content:
                        for tag in comment_inner_content.find_all('embed'):
                            embed_link = tag['src']
                            tag.replace_with("(Embed object pointing to " + embed_link + " removed from original post)")
                        for tag in comment_inner_content.find_all('iframe'):
                            iframe_link = tag['src']
                            tag.replace_with("(Iframe object pointing to " + iframe_link + " removed from original post)")
                        for tag in comment_inner_content.find_all('object'):
                            tag.replace_with("(Object tag removed from original post)")
                        for tag in comment_inner_content.find_all('param'):
                            tag.replace_with("(Param tag removed from original post)")
                    
                    comment_content = unicode(comment_inner_content)
                    comment_content = re.sub(r'<span.*?>|<\/span>', '', comment_content)
                    comment_content = re.sub(r'\sclass=".*?"', '', comment_content)
                    if not db.post_exists(comment_id):
                        db.process_post(comment_id, x, comment_name, comment_paws, comment_avatar, date, comment_content, "d")
                    else: 
                        db.update_post(comment_id, x, comment_name, comment_paws, date, comment_content, "d")                       
                else:
                    comment_avatar = re.search(r'background-image: url\(\'(.*)\?', tag.find(class_="avatar xxsmall")['style']).group(1)
                    db.process_removed(comment_id, x, comment_name, comment_avatar, date)
                        
            elif (tag['class'][3] == 'mine'):
                if tag['class'][4] != 'removed':
                    comment_paws = int(tag.find(class_="paw").find(class_="count").string)
                    comment_avatar = re.search(r'background-image: url\(\'(.*)\?', tag.find(class_="avatar small")['style']).group(1) 
                    comment_inner_content = tag.find(class_="html-content")
                    if comment_inner_content:
                        for tag in comment_inner_content.find_all('embed'):
                            embed_link = tag['src']
                            tag.replace_with("(Embed object pointing to " + embed_link + " removed from original post)")
                        for tag in comment_inner_content.find_all('iframe'):
                            iframe_link = tag['src']
                            tag.replace_with("(Iframe object pointing to " + iframe_link + " removed from original post)")
                        for tag in comment_inner_content.find_all('object'):
                            tag.replace_with("(Object tag removed from original post)")
                        for tag in comment_inner_content.find_all('param'):
                            tag.replace_with("(Param tag removed from original post)")
                    
                    comment_content = unicode(comment_inner_content)
                    comment_content = re.sub(r'<span.*?>|<\/span>', '', comment_content)
                    comment_content = re.sub(r'\sclass=".*?"', '', comment_content)
                    if not db.post_exists(comment_id):
                        db.process_post(comment_id, x, comment_name, comment_paws, comment_avatar, date, comment_content, "d")
                    else: 
                        db.update_post(comment_id, x, comment_name, comment_paws, date, comment_content, "d")      
                    
                else:
                    comment_avatar = re.search(r'background-image: url\(\'(.*)\?', tag.find(class_="avatar xxsmall")['style']).group(1)
                    db.process_removed(comment_id, x, comment_name, comment_avatar, date)
    print str(x)
    #progress(x, (x - start + 1), total)

blacklist.close()
db.close()
