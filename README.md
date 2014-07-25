Python scripts for scraping the myUMBC discussion forum. Functional, but currently need comments
and a general update since 2013. 

Requires:
BeautifulSoup 4
Dryscrape
MySQLdb
PyTagCloud

Also requires you to add your own config file, config.txt, with
credentials to myUMBC and a MySQL database, in the form of

[myumbc]
username = 
password = 

[database]
host = 
username = 
password = 
database = 
