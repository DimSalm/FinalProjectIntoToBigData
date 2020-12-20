import pandas as pd
import math
from math import isnan
import csv
import json
from numpyencoder import NumpyEncoder

# demographic aproach
# replace location with country and nan countries with 'other'
users_clean = pd.read_csv('BX_Users.csv')
ratings_clean = pd.read_csv('BX_Book_Ratings.csv')
users_clean['Country'] = users_clean['Location'].apply(lambda x: str(x).split(',')[-1])
user_demogr = users_clean.drop('Location',axis=1)
user_demogr['Country'] = user_demogr['Country'].str.replace(r'^\s*$',' other',regex=True)

# Warning! : You have to provide a subfolder into the main folder for each run
pc_directory = input('Enter computer directory to save the files\n(including / at the end,without "") : ').strip()

#print('All options of Countries: \n',user_demogr.groupby('Country')[['User_ID']].count())
# type the country you are interested in make recommendations
while True:
    x = input('Suggested options --> Spain , Italy , Canada , Austria , Australia , Usa , Portugal \n, Switzerland, United Kingdom, Netherlands, New Zealand , France, Malaysia \nEnter Location :   ')
    Location = ' ' + x.lower().strip()
    if user_demogr['Country'].str.contains(Location).any():
        print ("Country exists, starting recommender system...")
        break
    else:
        print('Country does not exist in dataset,\n please try again..')
        continue

# keep only the country chosen in ratings set
# transform ratings df to a nested dictionary
# keys are user ids and values is another dictionary with isbn as keys(all the books a user has read)
# and the value of that is a dictonary with 'Book_Rating' as key and the actual rating as value
user_by_country = user_demogr[user_demogr['Country'] == Location]
ratings = ratings_clean[ratings_clean['User_ID'].isin(user_by_country['User_ID'])]
pivot = ratings.groupby('User_ID')[['ISBN','Book_Rating']].apply(lambda x: x.set_index('ISBN').to_dict(orient='index')).to_dict()

# cosine similarity
def cosinecim(x,y):
    sum1 = 0.0
    sum2 = 0.0
    sum3 = 0.0
    for i in x:
        sum2 += x[i]['Book_Rating'] ** 2
        if i in y:
            sum1 += x[i]['Book_Rating']*y[i]['Book_Rating']
            sum3 += y[i]['Book_Rating']**2
    for j in y:
        if j not in x:
            sum3 += y[j]['Book_Rating']**2
    return sum1 / (math.sqrt(sum2)*math.sqrt(sum3))

# for each pair of users if they have a common isbn compute the cosine similarity
# else cosine similarity is zero and dont need computation
for user1 in pivot:
    for user2 in pivot:
        if set(pivot[user1]).intersection(pivot[user2]):
            with open(pc_directory + 'user_pairs_books.data','a') as paircsv:
                data = [user1, user2, cosinecim(pivot[user1], pivot[user2])]
                writer = csv.writer(paircsv)
                writer.writerow(data)
                #print(cosinecim(pivot[user1], pivot[user2]))

# read cosine similarities in a df and transform it to a nested dictionary
# keys are each user and values are all the similar to him users as keys
# and values another dictionary with 'similarity' as key and value the value of their similarity
similarities = pd.read_csv(pc_directory + 'user_pairs_books.data', names=['user1', 'user2', 'similarity'])
nNeighbors = 3
simpivot = similarities.groupby('user1')[['user2','similarity']].apply(lambda x: x.set_index('user2').to_dict(orient='index')).to_dict()

# for every user is similarities['user1'] find all the similar to him users in similarities['user2'] except himself
# sort them with highest similarity on top and take the nNeighbors highest as the most similar users to him to a json
for i in similarities['user1'].unique():
    df = similarities[(similarities['user1']==i) & (similarities['user2']!=i)].sort_values('similarity',ascending=False)
    data =[]
    data.append(i)
    for j in df.head(nNeighbors)['user2']:
        data.append(j)
    with open(pc_directory + 'neighbors_k_books.data', 'a') as jsonfiles:
        json.dump(data, jsonfiles, cls=NumpyEncoder)
    with open(pc_directory + 'neighborssql.data', 'a') as sql:
        writer = csv.writer(sql)
        writer.writerow(data)

# columns for every neighbor in order to read the next df
names = ['user']
for g in range(nNeighbors):
    names.append('neighbor'+str(g+1))

# read the neighbors in df and make a dictionary out of it
# keys are user ids,and values is a dictionary with keys neighbor1 of the user and value the neighbor of user
# neighbor2 for neighbor 2 of the user and value the neighbor of the user etc
nbs = pd.read_csv(pc_directory + 'neighborssql.data',header=None,names=names)
nb1 = nbs.set_index('user',drop=True).to_dict(orient='index')

# remove nan from nb1 dictionary,in case a user doesnt have as much neighbors as asked
nb = {key1: {key2: value2 for key2, value2 in value1.items() if not isnan(value2)} for key1, value1 in nb1.items()}

# for every neighbor of userid try the sum1 of prediction algorithm and if there is no rating of the neighbor
# for the itemid requested skip him and go to next neighbor
# if predictions exceed 0 or 10 correct them,if a user has no neighbors return his mean of ratings
def predict(userid, itemid ,ratings ,pivot, simpivot, nb):
    try:
        sum1, sum2 = 0.0, 0.0
        w1 = ratings.groupby('User_ID')[['Book_Rating']].mean()
        for user in nb[userid].values():
            try:
                sum1 += simpivot[userid][user]['similarity'] * (pivot[user][itemid]['Book_Rating'] - float(w1.loc[user]))
            except:
                sum1 = sum1
            sum2 += simpivot[userid][user]['similarity']
        if float(w1.loc[userid]) + sum1 / sum2 < 0:
            return 0
        elif float(w1.loc[userid]) + sum1 / sum2 > 10:
            return 10
        else:
            return float(w1.loc[userid]) + sum1 / sum2
    except:
        return float(w1.loc[userid])

# for every user and every book he has read predict the rating based on neighbors and store them in a csv
for u in pivot:
    for b in pivot[u]:
        pr = predict(u, b, ratings, pivot, simpivot, nb)
        preddata = [u, b, pr]
        with open(pc_directory + 'predictedratings.data', 'a') as predrat:
            writer = csv.writer(predrat)
            writer.writerow(preddata)

# make a df with userid, isbn, actual rating, predicted rating and deviation=actual - predicted
predictedratings = pd.read_csv(pc_directory + 'predictedratings.data',names=['User_ID','ISBN','Predicted_Rating'])

y = pd.merge(ratings,predictedratings,left_on=['User_ID','ISBN'],right_on=['User_ID','ISBN'])

y['Deviation'] = y.apply(lambda x: x.Predicted_Rating - x.Book_Rating, axis = 1)

# mean absolute error which takes 2 lists as input and computes the error
def mae(p, a):
    return sum(map(lambda x: abs(x[0] - x[1]), zip(p, a))) / len(p)

mean_absolute_error = mae(list(y['Predicted_Rating']),list(y['Book_Rating']))

print('\nmean absoluter error:  ',mean_absolute_error)

# root mean square error which takes 2 lists as input and computes the error
def rmse(p, a):
    return math.sqrt(sum(map(lambda x: (x[0] - x[1]) ** 2, zip(p, a))) / len(p))

mean_squared_error = rmse(list(y['Predicted_Rating']),list(y['Book_Rating']))

print('\nroot mean squared error  :',mean_squared_error)

paircsv.close()
jsonfiles.close()
sql.close()
predrat.close()
