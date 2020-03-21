import pandas as pd
from pymongo import MongoClient
from bson.objectid import ObjectId
client = MongoClient("mongodb+srv://edith:edith@edith-yqmat.gcp.mongodb.net/test?retryWrites=true&w=majority")
# Your database name (In my case it is test)
users_cl = client.test
# Your collection name(Mine is samples)
data_tb = users_cl.samples

df = pd.read_csv("sampledata.csv")
cols= df.columns
for i, row in enumerate(df.to_numpy()):
    data = {}
    for i, col in enumerate(cols[:8]):
        data[col] = row[i]
    data["userId"] = ObjectId(data["userId"][9:-1])
    data_tb.insert_one(data)