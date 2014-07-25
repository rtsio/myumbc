import time
import dryscrape
import MySQLdb
import re

class Scraper(object):

    def __init__(self):
        self.sess = dryscrape.Session(base_url = 'https://my.umbc.edu')
        self.sess.set_attribute('auto_load_images', False)
        self.sess.visit('/')

    def login(self, username, password):
        self.login = self.sess.at_xpath('//*[contains(text(), "Log In")]')
        self.login.click()
        self.user = self.sess.at_xpath('//*[@id="username"]')
        self.password = self.sess.at_xpath('//*[@id="password"]')
        self.user.set(username)
        self.password.set(password)
        self.user.form().submit()
	time.sleep(5)

    def valid(self, prefix, number):
        self.sess.visit('/' + prefix + '/' + str(number))
        self.html = self.sess.body()
	time.sleep(3)
        if "Loading comments..." in self.html:
            time.sleep(10)
            if "Loading comments..." in self.html:
                print "Could not load comments after 10 seconds for: " + number
                return False
        if "<p>We can't find the page you're looking for...</p>" in self.html:
            return False
        return True

    def gethtml(self):
        return self.sess.body()

class Database(object):
	
    def __init__(self, hostname, username, pw, db):
        self.host = hostname
        self.user = username
        self.password = pw
        self.database = db
        self.db = MySQLdb.connect(self.host, self.user, self.password, self.database, charset='utf8')
        self.cursor = self.db.cursor()

    def post_exists(self, postid):
        self.cursor.execute("""SELECT userid FROM `posts` WHERE postid=%s""", (postid))
        self.db.commit()
        if not self.cursor.rowcount:
            return False
        else:
            return True
        
    def process_post(self, postid, discussion, name, paws, avatar, date, content, ptype):
        self.cursor.execute("""SELECT * FROM `users` WHERE name=%s""", (name))
        self.db.commit()
        if not self.cursor.rowcount:
            self.cursor.execute("""SELECT MAX(id) FROM `users`""")
            self.db.commit()
            self.row = self.cursor.fetchone()[0]
            if not self.row:
                self.userid = 1
            else:
                self.userid = int(self.row) + 1
            self.cursor.execute("""INSERT INTO `users` VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", (self.userid, name, avatar, "none", 1, paws, 0, date))
            self.db.commit()
        else:
            self.row = self.cursor.fetchone()
            self.userid = int(self.row[0])
            self.currentposts = int(self.row[4])
            self.currentpaws = int(self.row[5])
            self.newposts = self.currentposts + 1
            self.newpaws = self.currentpaws + paws
            if "groups" in avatar:
                self.cursor.execute("""UPDATE users SET posts=%s, paws=%s, date=%s WHERE id=%s""", (self.newposts, self.newpaws, date, self.userid))
            else:
                self.cursor.execute("""UPDATE users SET avatar_link=%s, posts=%s, paws=%s, date=%s WHERE id=%s""", (avatar, self.newposts, self.newpaws, date, self.userid))
            self.db.commit()

        self.cursor.execute("""INSERT INTO posts(postid, userid, page, content, pawed, type) VALUES (%s, %s, %s, %s, %s, %s)""", (postid, self.userid, discussion, content, paws, ptype))
        self.db.commit()
   
    def update_post(self, postid, discussion, name, paws, date, content, ptype):
        self.need_update = False
        self.cursor.execute("""SELECT pawed, content from `posts` WHERE postid=%s""", (postid))
        self.db.commit()
        self.old_row = self.cursor.fetchone()
        self.old_paws = int(self.old_row[0])
        self.old_content = self.old_row[1]
        if self.old_paws != paws:
            self.need_update = True
        if self.old_content != content:
            self.need_update = True
        self.added_paws = paws - self.old_paws
        self.cursor.execute("""SELECT * FROM `users` WHERE name=%s""", (name))
        self.db.commit()
        self.row = self.cursor.fetchone()
        self.userid = int(self.row[0])
        self.currentpaws = int(self.row[5])
        self.newpaws = self.currentpaws + self.added_paws
        if self.need_update:
            self.cursor.execute("""UPDATE users SET paws=%s, date=%s WHERE id=%s""", (self.newpaws, date, self.userid))
            self.db.commit()
            self.cursor.execute("""UPDATE posts SET content=%s, pawed=%s WHERE postid=%s""", (content, paws, postid))
            self.db.commit()

    def process_removed(self, postid, page, name, avatar, date):
        self.cursor.execute("""SELECT * FROM `users` WHERE name=%s""", (name))
        self.db.commit()
        if not self.cursor.rowcount:
            self.cursor.execute("""SELECT MAX(id) FROM `users`""")
            self.db.commit()
            self.row = self.cursor.fetchone()[0]
            if not self.row:
                self.userid = 1
            else:
                self.userid = int(self.row) + 1
            self.cursor.execute("""INSERT INTO `users` VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", (self.userid, name, avatar, "none", 0, 0, 0, date))
            self.db.commit()        
        else:
            self.row = self.cursor.fetchone()
            self.userid = int(self.row[0])

        self.cursor.execute("""SELECT removed FROM `posts` WHERE postid=%s""", (postid))
        self.db.commit()

        if self.cursor.rowcount:
            self.row = self.cursor.fetchone()
            self.isremoved = int(self.row[0])
            if self.isremoved != 1:
                self.cursor.execute("""SELECT removed FROM `users` WHERE name=%s""", (name))
                self.db.commit()
                self.old_removed = self.cursor.fetchone()[0]
                self.new_removed = self.old_removed + 1
                self.cursor.execute("""UPDATE users SET removed=%s WHERE name=%s""", (self.new_removed, name))
                self.db.commit()
                self.cursor.execute("""UPDATE posts SET removed=%s WHERE postid=%s""", (0, postid))
                self.db.commit()
        else:
            self.cursor.execute("""SELECT removed FROM `users` WHERE name=%s""", (name))
            self.db.commit()
            self.old_removed = self.cursor.fetchone()[0]
            self.new_removed = self.old_removed + 1
            self.cursor.execute("""UPDATE users SET removed=%s WHERE name=%s""", (self.new_removed, name))
            self.db.commit()
            self.content = "We could not archive this comment before it was deleted."
            self.cursor.execute("""INSERT INTO posts(postid, userid, page, content, pawed, type, removed) VALUES (%s, %s, %s, %s, %s, %s, %s)""", (postid, self.userid, page, self.content, 0, "d", 1))
            self.db.commit()
			
    def last_user(self):
        self.cursor.execute("""SELECT MAX(id) FROM `users`""")
        self.db.commit()
        return self.cursor.fetchone()[0]
    
    def get_posts(self, user):
        self.cursor.execute("""SELECT content FROM `posts` WHERE userid=%s""", (user))
        self.db.commit()
        self.posts = u''
        for content in self.cursor.fetchall():
            self.posts += (content[0] + ' ')
            self.posts = re.sub(r'<[^<]*?/?>', ' ', self.posts)
            return self.posts
        
    def need_update(self, user, predicted_date):
        self.cursor.execute("""SELECT date, avatar_link FROM `users` WHERE id=%s""", (user))
        self.db.commit()
        row = self.cursor.fetchone()
        if row[0] == predicted_date:
            return 0
        else:
            return row[1]
        
    def insert_chart(self, user, url):
        self.cursor.execute("""UPDATE users SET chart_link=%s WHERE id=%s""", (url, user))
        self.db.commit()
		
    def close(self):
        self.db.close()
