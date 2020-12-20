import json
import hyperloglog
import probables
import math
import matplotlib.pyplot as plt
import csv
from pympler.asizeof import asizeof
import pandas as pd
import codecs

# Warning! put the directory where all other .py files and csv are.The main directory
pc_directory = input('Enter computer directory to save the files\n(including / at the end,without "") : ').strip()

# make a list with all json files
json_files=[]
for i in range(0, 46):
    json_files.append(pc_directory + 'twitter_world_cup_1m/tweets.json.' + str(i))

# function that returns corresponding value in tweets dict
def keyfunction(k):
    return tweets[k]

def keyfunction_hash(w):
    return hashtags[w]

# finds 100 users with the most tweets per 1000 tweets/finds final top 100 tweeters/finds the size of
# these 100 tweeters dict/finds the number of unique users that made a tweet
# whatever done for tweets also done for hashtags
# Both counting actual values and with cms
heavy_hitter = 100
cms_tweets = probables.CountMinSketch(confidence=0.9997, error_rate=0.0000278)
cms_hashtags = probables.CountMinSketch(confidence=0.999, error_rate=0.0001)
tweets = {}
hashtags = {}
thousands = -1
max_hitters = {}
max_hitters_cms = {}
max_hashtags = {}
max_hashtags_cms = {}
for file in json_files:
    myfile = open(file, 'r', encoding='utf-8')
    for line in myfile:
        data = json.loads(line)
        thousands += 1
        user_id = str(data['user']['id'])
        hashtag_path = data['entities']['hashtags']
        if user_id not in tweets:
            tweets[user_id] = 1
        else:
            tweets[user_id] += 1
        cms_tweets.add(user_id)
        try:
            for hashtag in range(len(hashtag_path)):
                if str(hashtag_path[hashtag]['text']) not in hashtags:
                    hashtags[str(hashtag_path[hashtag]['text'])] = 1
                else:
                    hashtags[str(hashtag_path[hashtag]['text'])] += 1
                cms_hashtags.add(str(hashtag_path[hashtag]['text']))
        except:
            continue
        if thousands%1000 == 0:
            max_hitters = {}
            max_hitters_cms = {}
            max_hashtags = {}
            max_hashtags_cms = {}
            for key1 in sorted(tweets, key=keyfunction, reverse=True)[:heavy_hitter]:
                max_hitters[key1] = tweets[key1]
            print(max_hitters)
            print("----------------------------------------------------------------")
            for (k1, v1) in max_hitters.items():
                max_hitters_cms[k1] = int(cms_tweets.check(k1))
                print(k1, v1, cms_tweets.check(k1), int(cms_tweets.check(k1)) - int(v1),"percentage error is:" + str(round(abs(v1 - cms_tweets.check(k1)) / v1 * 100)) + "%")
                print("----------------------------------------------------------------")
            print(max_hitters_cms)
            print("----------------------------------------------------------------")
            for key2 in sorted(hashtags, key=keyfunction_hash, reverse=True)[:heavy_hitter]:
                max_hashtags[key2] = hashtags[key2]
            print(max_hashtags)
            print("----------------------------------------------------------------")
            for (k2, v2) in max_hashtags.items():
                max_hashtags_cms[k2] = int(cms_hashtags.check(k2))
                print(k2, v2, cms_hashtags.check(k2), int(cms_hashtags.check(k2)) - int(v2),"percentage error is:"+str(round(abs(v2-cms_hashtags.check(k2))/v2*100))+"%")
                print("----------------------------------------------------------------")
            print(max_hashtags_cms)
            print("----------------------------------------------------------------")

# same computations but at the end of the stream
for key3 in sorted(tweets, key=keyfunction, reverse=True)[:heavy_hitter]:
    max_hitters[key3] = tweets[key3]
for (k3, v3) in max_hitters.items():
    max_hitters_cms[k3] = int(cms_tweets.check(k3))
for key4 in sorted(hashtags, key=keyfunction_hash, reverse=True)[:heavy_hitter]:
    max_hashtags[key4] = hashtags[key4]
for (k4, v4) in max_hashtags.items():
    max_hashtags_cms[k4] = int(cms_hashtags.check(k4))

# size of the dictionaries and cms / max hitters
print("----------------------------------------------------------------")
print("The users that made the most tweets are:" + str(max_hitters))
print("----------------------------------------------------------------")
print("Size of tweets: " + str(asizeof(tweets)) + "bytes")
print("----------------------------------------------------------------")
print("Size of cms_tweets: " + str(asizeof(cms_tweets)) + "bytes")
print("----------------------------------------------------------------")
print("The users that made the most tweets based on cms are:" + str(max_hitters_cms))
print("----------------------------------------------------------------")
print("----------------------------------------------------------------")
print("The most popular hashtags in tweets are: "+str(max_hashtags))
print("----------------------------------------------------------------")
print("Size of hashtags: " + str(asizeof(hashtags)) + "bytes")
print("----------------------------------------------------------------")
print("Size of cms_tweets: " + str(asizeof(cms_hashtags)) + "bytes")
print("----------------------------------------------------------------")
print("The users that made the most hashtags based on cms are:" + str(max_hashtags_cms))
print("----------------------------------------------------------------")

# save all the previous results in csv
# codec is used because of problem with unicode in hashtags 
with open(pc_directory + 'user-counter.csv', 'w') as f:
    w = csv.writer(f)
    w.writerows(tweets.items())

with open(pc_directory + 'cmstweets.csv', 'w') as g:
    for j in tweets:
        g.write(str(j) + ',' + str(cms_tweets.check(str(j))) + '\n')

with codecs.open(pc_directory + 'hashtag-counter.csv', 'w', encoding="utf-8") as f:
    for key, value in hashtags.items():
        f.write(key+','+str(value)+'\n')

with codecs.open(pc_directory + 'hashtag-counter-cms.csv', 'w', encoding="utf-8") as f2:
    for i in hashtags:
        f2.write(i+','+str(cms_hashtags.check(i))+'\n')


# compute unique users with a counting algirithm and with hyperlLogLog
hll_tweets = hyperloglog.HyperLogLog(0.01)
hll_hashtags = hyperloglog.HyperLogLog(0.01)
count_users = {}
count_hash = {}
for file in json_files:
    myfile=open(file, 'r', encoding='utf-8')
    for line in myfile:
        data = json.loads(line)
        if data['user']['id'] not in count_users:
            count_users[data['user']['id']]=1
        hll_tweets.add(str(data['user']['id']))
        try:
            for hashtag2 in range(len(data['entities']['hashtags'])):
                if data['entities']['hashtags'][hashtag2]['text'] not in count_hash:
                    count_hash[data['entities']['hashtags'][hashtag2]['text']] = 1
                hll_hashtags.add(str(data['entities']['hashtags'][hashtag2]['text']))
        except:
            continue

# print size of every method used/ one with the counting algorith and one with hll
print("----------------------------------------------------------------")
print("The number of unique users that posted a tweet is:" + str(len(count_users)))
print("----------------------------------------------------------------")
print('Approximate number of distinct tweeters: {0}'.format(math.ceil(hll_tweets.card())))
print("----------------------------------------------------------------")
print("Size of hll_tweets: " + str(asizeof(hll_tweets)) + "bytes")
print("----------------------------------------------------------------")
print("Size of count unique users: " + str(asizeof(count_users)) + "bytes")
print("----------------------------------------------------------------")
print("The number of unique hashtags posted on tweeter are: "+ str(len(count_hash)))
print("----------------------------------------------------------------")
print('Approximate number of distinct hashtags: {0}'.format(math.ceil(hll_hashtags.card())))
print("----------------------------------------------------------------")
print("Size of hll_tweets: " + str(asizeof(hll_hashtags)) + "bytes")
print("----------------------------------------------------------------")
print("Size of count unique hastags: " + str(asizeof(count_hash)) + "bytes")
print("----------------------------------------------------------------")

#functions for mean absolute error and root mean squared error
def mae(p, a):
    return sum(map(lambda x: abs(x[0] - x[1]), zip(p, a))) / len(p)

def rmse(p, a):
    return math.sqrt(sum(map(lambda x: (x[0] - x[1]) ** 2, zip(p, a))) / len(p))

#reports the change % between the actual value and the approximate with hll
def change(a, p):
    return ((a-p)/a)*100

# some plots for the report
useractual = pd.read_csv(pc_directory + 'user-counter.csv',names=['keys','actual'],delimiter=',').astype(int)
usercms = pd.read_csv(pc_directory + 'cmstweets.csv',names=['keys','cms'],delimiter=',').astype(int)
users = pd.merge(useractual,usercms)

hashactual = pd.read_csv(pc_directory + 'hashtag-counter.csv',names=['keys','actual'],delimiter=',')
hashcms = pd.read_csv(pc_directory + 'hashtag-counter-cms.csv',names=['keys','cms'],delimiter=',')
hashcms['cms'].astype(int)
hashactual['actual'].astype(int)
hashes = pd.merge(hashcms,hashactual)
'''
plt.plot('actual', data=users, marker='o', markersize=15, color='blue', linewidth=5)
plt.plot('cms', data=users, marker='x', color='red', linewidth=1, markersize=10,linestyle='dashed')
plt.show()

plt.plot('actual', data=hashes, marker='o', markersize=15, color='blue', linewidth=5)
plt.plot('cms', data=hashes, marker='x', color='red', linewidth=1, markersize=10,linestyle='dashed')
plt.show()
'''
print("----------------------------------------------------------------")
mean_absolute_error1 = mae(list(users['actual']), list(users['cms']))
print('mean absolute error for users:  ', mean_absolute_error1)
print("----------------------------------------------------------------")
mean_squared_error1 = rmse(list(users['actual']), list(users['cms']))
print('root mean squared error for users :', mean_squared_error1)
print("----------------------------------------------------------------")
change1 = change(len(hll_tweets), len(count_users))
print('Change from the actual value for unique tweets:  ', change1,'%')
print("----------------------------------------------------------------")
mean_absolute_error2 = mae(list(hashes['actual']), list(hashes['cms']))
print('mean absolute error for hashtags:  ', mean_absolute_error2)
print("----------------------------------------------------------------")
mean_squared_error2 = rmse(list(hashes['actual']), list(hashes['cms']))
print('root mean squared error for hashtags :', mean_squared_error2)
print("----------------------------------------------------------------")
change2 = change(len(hll_hashtags),len(count_hash))
print('Change from the actual value for unique hashtags:  ', change2,'%')
print("----------------------------------------------------------------")
