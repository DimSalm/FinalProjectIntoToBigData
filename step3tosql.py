import mysql.connector

user = input('Enter username: ')
password = input('Enter password: ')

conn = mysql.connector.connect(user=user, password=password, host='127.0.0.1', allow_local_infile=True)

cursor = conn.cursor(buffered=True)

cursor.execute("drop database if exists books")
cursor.execute("CREATE DATABASE books")
cursor.execute("USE books")

# create all the tables needed
cursor.execute("CREATE TABLE BX_Books (ISBN varchar(13) NOT NULL PRIMARY KEY,Book_Title varchar(255) default NULL,Book_Author varchar(255) default NULL,Year_Of_Publication int(10) default NULL,Publisher varchar(255) default NULL)")
cursor.execute("CREATE TABLE BX_Users (User_ID int(11) NOT NULL PRIMARY KEY default '0',Location varchar(250) default NULL,Age int(11) default NULL)")
cursor.execute("CREATE TABLE BX_Book_Ratings (User_ID int(11) NOT NULL default '0',ISBN varchar(13) NOT NULL,Book_Rating int(11) NOT NULL default '0',FOREIGN KEY (ISBN) REFERENCES BX_Books(ISBN),FOREIGN KEY (User_ID) REFERENCES BX_Users(User_ID),PRIMARY KEY (User_ID,ISBN))")
cursor.execute("CREATE TABLE user_neighbors (Userid int(11) NOT NULL PRIMARY KEY,neighbor1 INT(11) NOT NULL,neighbor2 INT(11) NOT NULL)")
cursor.execute("CREATE TABLE user_pairs (User_1 int(11) NOT NULL,User_2 INT(11) NOT NULL,Similarity FLOAT(8,7) default NULL,PRIMARY KEY(User_1,User_2))")

# ingest the csv files from step2recommender
# if all files are not in the same directory change the load data local infile destination
cursor.execute("""
load data local infile 'BX_Users.csv' 
into table BX_Users 
fields terminated by ',' OPTIONALLY ENCLOSED BY '"'
lines terminated by '\r\n' 
ignore 1 lines;
""")
cursor.execute("""
load data local infile  'BX_Books.csv'
into table BX_Books 
fields terminated by ',' OPTIONALLY ENCLOSED BY '"' 
lines terminated by '\r\n' 
ignore 1 lines;
""")
cursor.execute("""
load data local infile 'BX_Book_Ratings.csv' 
into table BX_Book_Ratings 
fields terminated by ',' 
lines terminated by '\r\n' 
ignore 1 lines;
""")
cursor.execute("""
load data local infile 'user_pairs_books.data' 
into table user_pairs 
fields terminated by ',' OPTIONALLY ENCLOSED BY '"'
lines terminated by '\r\n' 
ignore 0 lines;
""")
cursor.execute("""
load data local infile 'neighborssql.data' 
into table user_neighbors 
fields terminated by ',' OPTIONALLY ENCLOSED BY '"'
lines terminated by '\r\n' 
ignore 0 lines;
""")

conn.commit()
cursor.close()
conn.close()