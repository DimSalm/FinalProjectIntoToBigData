import pandas as pd
import warnings
import matplotlib.pyplot as plt

# read the csv as dataframes
books = pd.read_csv('BX-Books.csv',delimiter=';',encoding='Latin-1',quotechar='"',escapechar='\\')
ratings = pd.read_csv('BX-Book-Ratings.csv',delimiter=';',encoding='Latin-1')
users = pd.read_csv('BX-Users.csv',delimiter=';',encoding='Latin-1')

# info regarding each csv size,general information,statistics
print(books.info(memory_usage='deep'))
print('books rows,columns and info: ',books.shape)
print(books['Year-Of-Publication'].describe())
print("----------------------------------------------------------------")
print(ratings.info(memory_usage='deep'))
print('book ratings rows,columns and info: ',ratings.shape)
print(ratings['Book-Rating'].describe())
print("----------------------------------------------------------------")
print(users.info(memory_usage='deep'))
print('users rows,columns and info: ',users.shape)
print(users['Age'].describe())

# clean BX-Books:year of puplication for the years bigger than 2020
booksclean1 = books[books['Year-Of-Publication'] <= 2020]

# clean BX-Books:drop columns with urls(no needed for the analysis)
booksclean2 = booksclean1.drop(['Image-URL-S','Image-URL-M','Image-URL-L'], axis=1)

# clean BX-Books: drop isbn where not 9 numeric digits and then X or x(there are no 13 digits isbn)
warnings.filterwarnings("ignore", 'This pattern has match groups')
filter1 = booksclean2['ISBN'].str.contains("(\d{9}(\d|X|x))")
booksclean3 = booksclean2[filter1]
#print(booksclean3)

# clean BX-Book-Ratings: isbn not valid in ratings
filter2 = ratings['ISBN'].str.contains("(\d{9}(\d|X|x))")
ratingsclean1 = ratings[filter2]
#print(ratingsclean1)

# clean users: drop age where age>90 and age<14 as it doent gives us much information
usersclean1 = users[~(users['Age'] > 90)]
usersclean2 = usersclean1[~(usersclean1['Age'] < 14)]
#print(usersclean2)

# keep only the common values from every dataframe after the cleaning
ratings_clean1 = ratingsclean1[ratingsclean1['ISBN'].isin(booksclean3['ISBN'])]
users_clean = usersclean2[usersclean2['User-ID'].isin(ratings_clean1['User-ID'])]
#print("----------------------------------------------------------------")
#print('BX-Users clean:\n',users_clean)

ratings_clean = ratings_clean1[ratings_clean1['User-ID'].isin(users_clean['User-ID'])]
#print("----------------------------------------------------------------")
#print('BX-Book-Ratings clean:\n', ratings_clean)

books_clean = booksclean3[booksclean3['ISBN'].isin(ratings_clean['ISBN'])]
#print("----------------------------------------------------------------")
#print('BX-Books clean:\n',books_clean)

# book popularity = books ordered by "how many times has a book been read"
bookpop = ratings_clean.groupby(['ISBN'])[['Book-Rating']].count().sort_values(['Book-Rating'],ascending=False)
print("----------------------------------------------------------------")
print('Book popularity:\n', bookpop)

# # this is a plot for the presentation
#bookpop.reset_index().head(100).plot(x='ISBN', y='Book-Rating',kind='scatter')
#plt.show()

# author popularity = authors ordered by "how many users have read their books"
bru1 = pd.merge(books_clean,ratings_clean)
authorpop = bru1.groupby(['Book-Author'])[['Book-Rating']].count().sort_values(['Book-Rating'],ascending=False)
print("----------------------------------------------------------------")
print('Author popularity:\n', authorpop)

# # this is a plot for the presentation
#useractivitybefore = ratings.groupby(['User-ID'])[['Book-Rating']].count().sort_values(['Book-Rating'],ascending=False)
#useractivitybefore.reset_index().head(1000).plot(x='User-ID',y='Book-Rating',kind='scatter')
#plt.show()

# How many books each age group has read
bru2 = pd.merge(users_clean,ratings_clean)
agegroups = pd.cut(bru2['Age'], bins=[13, 30, 45, 60, 75, 90])
ageranges = bru2.groupby(agegroups)[['Book-Rating']].count().sort_values(['Book-Rating'],ascending=False)
print("----------------------------------------------------------------")
print('Books read per Age group:\n', ageranges)

# BX-Book-Rating Outlier detection where rating=0, we only want explicit ratings
booksread = ratings_clean[~(ratings_clean['Book-Rating']==0)]

# BX-User outlier detection: take out users with a lot of reading activity distance
# than the others by throwing out those that have more than the mean of last 10
usersread2 = booksread.groupby('User-ID')[['Book-Rating']].count()
usersread3 = usersread2[usersread2['Book-Rating'] < int(usersread2.sort_values('Book-Rating',ascending=False).head(10).mean())].reset_index()
ratingsfinal2 = booksread[booksread['User-ID'].isin(usersread3['User-ID'])]

# BX-User outlier detection where users with one rating goes out if the rating is in a book that has been read
# less than 2 times the average in order to be a popular book
ratingsfinal3 = ratingsfinal2.groupby('User-ID')[['Book-Rating']].count()
ratingsfinal4 = ratingsfinal3[ratingsfinal3['Book-Rating']==1].reset_index()
x2 = ratingsfinal2.groupby('ISBN')[['Book-Rating']].count().sort_values('Book-Rating')
x4 = x2[x2['Book-Rating'] < 2*ratingsfinal2.groupby('ISBN')['Book-Rating'].count().mean()].reset_index()
x6 = ratingsfinal2[ratingsfinal2['ISBN'].isin(x4['ISBN'])]
x7 = x6[x6['User-ID'].isin(ratingsfinal4['User-ID'])]
ratingsoutliers = ratingsfinal2[~ratingsfinal2['User-ID'].isin(x7['User-ID'])]

# BX-Book-Rating outlier detection where number of times the book has been read is above average
booksread2 = ratingsoutliers.groupby(['ISBN'])[['Book-Rating']].count()
booksread3 = booksread2[booksread2['Book-Rating'] > ratingsoutliers.groupby('ISBN')['Book-Rating'].count().mean()].reset_index()
ratingsfinal = ratingsoutliers[ratingsoutliers['ISBN'].isin(booksread3['ISBN'])]

# keep only the commons after outlier detection
usersfinal = users_clean[users_clean['User-ID'].isin(ratingsfinal['User-ID'])]
booksfinal = books_clean[books_clean['ISBN'].isin(ratingsfinal['ISBN'])]


# dataframes with renamed colomnus so that sql recognize them
booksfinal = booksfinal.rename(columns={'Book-Author':'Book_Author','Book-Title':'Book_Title','Year-Of-Publication':'Year_Of_Publication'})
ratingsfinal = ratingsfinal.rename(columns={'User-ID':'User_ID','Book-Rating':'Book_Rating'})
usersfinal = usersfinal.rename(columns={'User-ID':'User_ID'})
print("----------------------------------------------------------------")
print(booksfinal)
print("----------------------------------------------------------------")
print(ratingsfinal)
print("----------------------------------------------------------------")
print(usersfinal)
print("----------------------------------------------------------------")
# # this is for the presentation
#print(booksfinal.info(memory_usage='deep'))
#print(ratingsfinal.info(memory_usage='deep'))
#print(usersfinal.info(memory_usage='deep'))


# # this is a plot for the presentation
#bookpopafter = ratingsfinal.groupby(['ISBN'])[['Book_Rating']].count().sort_values(['Book_Rating'],ascending=False)
#bookpopafter.reset_index().head(100).plot(x='ISBN', y='Book_Rating',kind='scatter')
#plt.show()
#useractivityafter = ratingsfinal.groupby(['User_ID'])[['Book_Rating']].count().sort_values(['Book_Rating'],ascending=False)
#useractivityafter.reset_index().head(1000).plot(x='User_ID',y='Book_Rating',kind='scatter')
#plt.show()

# dataframes to csv
booksfinal.to_csv(r'C:\Users\dimsa\Desktop\ProjectBigData\BX_Books.csv',index=False,na_rep='NULL')
ratingsfinal.to_csv(r'C:\Users\dimsa\Desktop\ProjectBigData\BX_Book_Ratings.csv',index=False,na_rep='NULL')
usersfinal.to_csv(r'C:\Users\dimsa\Desktop\ProjectBigData\BX_Users.csv',index=False,na_rep='NULL')