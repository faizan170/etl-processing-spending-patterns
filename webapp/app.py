from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import json

client = MongoClient("mongodb+srv://edith:edith@edith-yqmat.gcp.mongodb.net/test?retryWrites=true&w=majority")
# Your database name (In my case it is test)
users_cl = client.test
# Your collection name(Mine is samples)
data_tb = users_cl.samples

def jsonifyData(data):
    my_json = data.decode('utf8')
    data = json.loads(my_json)
    return data

def valHelper(data, val532, excludeCal):
    newData = []
    for val in data:
        if val["532"].lower() == val532.lower() and val["excludedFromCalc"] == excludeCal:
            newData.append(val["amount"])
    return newData

def process532(data):
    result = {}
    result['Needs_Nominal'] = round(abs(sum(valHelper(data, "NEEDS", False))),2)
    result['Wants_Nominal'] = round(abs(sum(valHelper(data, "WANTS", False))), 2)
    result['Goals_Nominal'] = round(abs(sum(valHelper(data, "GOALS", False))), 2)
    result['MoneyIn_Nominal'] = round(sum(valHelper(data, "MoneyIn-Transfer", False) + valHelper(data, "Income", False)), 2)
    result['Balance_Nominal'] = round(result['MoneyIn_Nominal'] - (result['Needs_Nominal'] + result['Wants_Nominal'] + result['Goals_Nominal']), 2)
    
    if result['Balance_Nominal'] > 0:
        result['Needs_percent'] = str(round(result['Needs_Nominal'] / sum([result['Needs_Nominal'], result['Wants_Nominal'], result['Goals_Nominal'], result['Balance_Nominal']]) * 100)) + "%"
        result['Wants_percent'] = str(round(result['Wants_Nominal'] / sum([result['Needs_Nominal'], result['Wants_Nominal'], result['Goals_Nominal'], result['Balance_Nominal']]) * 100)) + "%"
        result['Goals_percent'] = str(round(result['Goals_Nominal'] / sum([result['Needs_Nominal'], result['Wants_Nominal'], result['Goals_Nominal'], result['Balance_Nominal']]) * 100)) + "%"
        result['Balance_percent'] = str(round(result['Balance_Nominal'] / sum([result['Needs_Nominal'], result['Wants_Nominal'], result['Goals_Nominal'], result['Balance_Nominal']]) * 100)) + "%"
    else:
        result['Needs_percent'] = str(round(result['Needs_Nominal'] / sum([result['Needs_Nominal'], result['Wants_Nominal'], result['Goals_Nominal']]) * 100)) + "%"
        result['Wants_percent'] = str(round(result['Wants_Nominal'] / sum([result['Needs_Nominal'], result['Wants_Nominal'], result['Goals_Nominal']]) * 100)) + "%"
        result['Goals_percent'] = str(round(result['Goals_Nominal'] / sum([result['Needs_Nominal'], result['Wants_Nominal'], result['Goals_Nominal']]) * 100)) + "%"
        result['Balance_percent'] = "0%"
    
    return result



def calculateUser532(userId, monthGet=""):
    # Get all transactions for that user
    transactions = list(data_tb.find({"userId" : ObjectId(userId)}))
    print("Total transactions:", len(transactions))
    # Get total months from data
    totalMonths = list(set([a["madeOn"].split("/")[1] + "/" + a["madeOn"].split("/")[2] for a in transactions]))
    totalMonths.sort()
    totalMonths.sort(key=lambda x: x[1], reverse=True)
    print(totalMonths)
    finalOutPut = []
    for month in totalMonths:
        listData = []
        # If month is not passed to function. Then get all data otherwise get single month data
        if monthGet != "":
            if monthGet != month:
                continue
        for tran in transactions:
            if tran["madeOn"].split("/")[1] + "/" + tran["madeOn"].split("/")[2] == month:
                listData.append(tran)
        resp = process532(listData)
        
        # Format data for datetime
        split = month.split("/")
        if len(split[0]) == 1: split[0] = "0" + split[0]
        if len(split[1]) == 2: split[1] = "20" + split[1]
        
        # Return final output
        finalOutPut.append([datetime.strptime(f"{split[0]} {split[1]}", "%m %Y").strftime("%B %Y"),resp])
    return finalOutPut

def calculateMonthlyCategoryTotal(userId, monthGet=""):
    transactions = list(data_tb.find({"userId" : ObjectId(userId)}))
    totalMonths = list(set([(int(a["madeOn"].split("/")[1]), int(a["madeOn"].split("/")[2])) for a in transactions]))
    totalMonths.sort()
    totalMonths.sort(key=lambda x: x[1])
    finalOutPut = []
    for month in totalMonths:
        data = {}
        if monthGet != "":
            if monthGet != f"{month[0]}/{month[1]}":
                continue
        for tran in transactions:
            tm = tran["madeOn"].split("/")
            if f"{tm[1]}/{tm[2]}" != f"{month[0]}/{month[1]}":
                continue
            if tran["category"] in data:
                data[tran["category"]].append(tran["amount"])
            else:
                data[tran["category"]] = [tran["amount"]]
        for key in data:
            data[key] = abs(sum(data[key]))
        
        split = [str(month[0]), str(month[1])]
        if len(split[0]) == 1: split[0] = "0" + split[0]
        if len(split[1]) == 2: split[1] = "20" + split[1]
        
        finalOutPut.append([datetime.strptime(f"{split[0]} {split[1]}", "%m %Y").strftime("%B %Y"), data])
    return finalOutPut

app = Flask(__name__)

@app.route("/")
def mainRoute():
    return "Application is working"

@app.route("/calculate-532", methods=["POST"])
def calculateData():
    data = jsonifyData(request.data)
    month = ""
    if "month" in data: month = data["month"]
    return jsonify(calculateUser532(data["userId"], month))

@app.route("/calculate-category", methods=["POST"])
def calculateDataCat():
    data = jsonifyData(request.data)
    month = ""
    if "month" in data: month = data["month"]
    return jsonify(calculateMonthlyCategoryTotal(data["userId"], month))




if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")