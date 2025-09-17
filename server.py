import os
import copy
import httpx
import time
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import pickle
from collections import UserDict

page_format = {
    "mode": 0,
    "model": 0,
    "nutri": [0, 0, 0, 0, "", ""],
    "state": 0,
    "ip": "",
    "tfidf": None,
    "corpus": ["weather", "news"],
    "vcr": None,
    "llmcontext": "",
    "city": "",
    "comban": 0,
    "botban": 0
}


class dynamicdb(UserDict):
    global page_format

    def __init__(self, *args, mode="dict", **kwargs):
        super().__init__(*args, **kwargs)
        self.mode = mode
        self.keyslastacc = []
        self.keyslist = []
        self.lenallowed = -1

    def __getitem__(self, key):
        try:
            ind = self.keyslist.index(key)
            self.keyslastacc[ind] = time.time() * 1000
        except Exception:
            print("Error: ", key)
        print("Cache List: ",self.keyslist)
        print("Cache Last Acc Time: ",self.keyslastacc)
        temp = {}
        if self.mode == "list":
            super().__getitem__(key)
            with open(f"{key}.dat", "wb") as file:
                pickle.dump(super().__getitem__(key), file)
            return super().__getitem__(key)
        for k, v in super().__getitem__(key).items():
            if k != "tfidf" and k != "vcr":
                temp[k] = v
        with open(f"{key}.dat", "wb") as file:
            pickle.dump(temp, file)
        return super().__getitem__(key)

    def __contains__(self, key):
        return os.path.exists(f"{key}.dat")

    def __setitem__(self, key, value):
        if key not in self.keyslist:
            if self.lenallowed < 10:
                self.lenallowed = self.lenallowed + 1
                print("Adding: ", key)
                self.keyslist.append(key)
                self.keyslastacc.append(time.time() * 1000)
            else:
                ind = self.keyslastacc.index(min(self.keyslastacc))
                print("--------------------------------------------------")
                print("Deleting: ", self.keyslist[ind])
                print("--------------------------------------------------")
                updt = self[self.keyslist[ind]]
                del self[self.keyslist[ind]]
                self.keyslastacc[ind] = time.time() * 1000
                self.keyslist[ind] = key
        super().__setitem__(key, value)

    def __missing__(self, key):
        print("Missing: ", key)
        if key not in self.keyslist:
            if self.lenallowed < 10:
                self.lenallowed = self.lenallowed + 1
                print("Adding: ", key)
                self.keyslist.append(key)
                self.keyslastacc.append(time.time() * 1000)
            else:
                ind = self.keyslastacc.index(min(self.keyslastacc))
                print("--------------------------------------------------")
                print("Deleting: ", self.keyslist[ind])
                updt = self[self.keyslist[ind]]
                print("--------------------------------------------------")
                del self[self.keyslist[ind]]

                self.keyslastacc[ind] = time.time() * 1000
                self.keyslist[ind] = key

        if not os.path.exists(f"{key}.dat"):
            if self.mode == "list":
                self[key] = []
            else:
                self[key] = copy.deepcopy(page_format)
            return self[key]
        print(f"Querying {key} from dat file")

        with open(f"{key}.dat", "rb") as file:
            temp = pickle.load(file)
            self[key] = temp
            self[key]["tfidf"] = None
            self[key]["vcr"] = None
            return self[key]


combanulist = []
apiswitch = 0
llmcontext = ""

switch = 0
model1 = joblib.load("crop_prediction.pkl")
modi = pickle.load(open('classifier.pkl', 'rb'))

fert = pickle.load(open('fertilizer.pkl', 'rb'))

res = fert.classes_[modi.predict([[50, 0, 7, 76, 65, 65]])]
print(res)
df = pd.read_csv("state_month_avg_rainfall.csv")
df = df.set_index("state_name")
db = dynamicdb({})
everyMod = [["REDIRECT_TO_MODEL1", 4], ["REDIRECT_TO_MODEL2", 6]]
load_dotenv()
OPENAI_API_KEY = [os.getenv("OPENROUTER_API_KEY")]

OPENAI_MODEL = os.getenv("OPENROUTER_MODEL",
                         "gpt-4o-mini")  # multilingual model
chat_history = dynamicdb({}, mode="list")


def predictmod(dbuid):

    geocode = httpx.get("http://ip-api.com/json/" + dbuid["ip"])
    dat = geocode.json()
    print(dat)
    state = dat["regionName"]
    city = dat["city"]
    monthno = datetime.now().month
    rainfall = df.loc[state.replace(" ", "").lower(
    ), str(monthno)] + df.loc[state.replace(" ", "").lower(
    ), str((monthno + 1 - 1) % 12 +
           1)] + df.loc[state.replace(" ", "").lower(),
                        str((monthno + 2 - 1) % 12 +
                            1)] + df.loc[state.replace(" ", "").lower(),
                                         str((monthno + 3 - 1) % 12 + 1)]
    weather = httpx.get(
        "http://api.weatherapi.com/v1/current.json?key=00875ab90fb54517a57132130250309&q="
        + city + "&aqi=no")
    weatherdat = weather.json()

    humidity = weatherdat["current"]["humidity"]
    resp = model1.predict(
        [[
            dbuid["nutri"][0], dbuid["nutri"][1], dbuid["nutri"][2],
            dbuid["nutri"][3], rainfall, humidity
        ]]
    )[0] + " is the best crop supporting your soil" or "No crop is suitable for your soil"
    if dbuid["model"] == 0:
        return resp

    if dbuid["model"] == 1:
        match dbuid["nutri"][4]:
            case "Black":
                dbuid["nutri"][4] = 0
            case "Clayey":
                dbuid["nutri"][4] = 1
            case "Loamy":
                dbuid["nutri"][4] = 2
            case "Red":
                dbuid["nutri"][4] = 3
            case "Sandy":
                dbuid["nutri"][4] = 4
            case _:
                return "Invalid Soil Type"
        crop = dbuid["nutri"][5]
        match dbuid["nutri"][5]:
            case "Barley":
                dbuid["nutri"][5] = 0
            case "Cotton":
                dbuid["nutri"][5] = 1
            case "Groundnuts":
                dbuid["nutri"][5] = 2
            case "Maize":
                dbuid["nutri"][5] = 3
            case "Millet":
                dbuid["nutri"][5] = 4
            case "Oil Seed":
                dbuid["nutri"][5] = 5
            case "Paddy":
                dbuid["nutri"][5] = 6
            case "Pulses":
                dbuid["nutri"][5] = 7
            case "Sugarcane":
                dbuid["nutri"][5] = 8
            case "Tobacco":
                dbuid["nutri"][5] = 9
            case "Wheat":
                dbuid["nutri"][5] = 10
            case "Cofee":
                dbuid["nutri"][5] = 11
            case "Rajma":
                dbuid["nutri"][5] = 12
            case "Orange":
                dbuid["nutri"][5] = 13
            case "Annardana":
                dbuid["nutri"][5] = 14
            case "Rice":
                dbuid["nutri"][5] = 15
            case "Watermellon":
                dbuid["nutri"][5] = 16
            case _:
                return "Crop data yet not available"
        print("\n")
        print("\n")
        print("\n")
        print("\n")
        print("\n")
        print("\n")
        print("\n")
        print([
            int(humidity),
            int(dbuid["nutri"][4]),
            int(dbuid["nutri"][5]),
            int(dbuid["nutri"][0]),
            int(dbuid["nutri"][2]),
            int(dbuid["nutri"][1])
        ])
        print("\n")
        print("\n")
        print("\n")
        print("\n")
        print("\n")
        resp += ". But if you want to grow " + crop + " you need to add " + fert.classes_[
            modi.predict([[
                int(humidity),
                int(dbuid["nutri"][4]),
                int(dbuid["nutri"][5]),
                int(dbuid["nutri"][0]),
                int(dbuid["nutri"][2]),
                int(dbuid["nutri"][1])
            ]])][0]

        return resp


def call_llm(user_message: str) -> str:
    global apiswitch
    global switch
    global llmcontext
    apiswitch = apiswitch + 1
    print(23)
    print(llmcontext)
    #if not OPENAI_API_KEY:
    #  return "No LLM API key provided."

    system_prompt = llmcontext + """
You are an agriculture related chatbot.
Reply in english no matter the language of user . Response in following format only:


Text:<Your Respone Here(Dont use enter or line breaks)>
<option number>:<Options>



Always provide options, Remember to start each option from a new line,
or if you feel regardless of language if farmer is asking about which crop to plant
then write only this REDIRECT_TO_MODEL1 only and nothing else
or if you feel regadless of language if farmer wants to plant a specific crop or wants to know about fertilizer
then write only this REDIRECT_TO_MODEL2 only and nothing else
"""
    system_prompt_sms = '''
    You are an agriculture related sms bot. Resolve the query .Reply in the same language as that of user Default Language:English .

    '''
    try:
        headers = {
            "Authorization":
            f"Bearer {OPENAI_API_KEY[apiswitch%len(OPENAI_API_KEY)]}",
            "Content-Type": "application/json"
        }
        print(OPENAI_API_KEY[apiswitch % len(OPENAI_API_KEY)])
        if switch == 1:
            system_prompt = system_prompt_sms
        elif switch == 3:
            system_prompt = "If you find any offensive , abusive language or untrue and balantly false fact or too good to be true things in the user message then print REDACTED only and nothing else otherwise print OK only"

        body = {
            "model":
            OPENAI_MODEL,
            "messages": [{
                "role": "system",
                "content": system_prompt
            }, {
                "role": "user",
                "content": user_message
            }],
            "temperature":
            0.2
        }

        r = httpx.post("https://openrouter.ai/api/v1/chat/completions",
                       headers=headers,
                       json=body,
                       timeout=30)
        r.raise_for_status()
        data = r.json()
        reply = data["choices"][0]["message"]["content"]
        switch = 0
        return reply
    except Exception as e:
        return f"Error: {e}"


app = Flask(__name__)


@app.route("/<adminquery>", methods=["GET"])
def admindata(adminquery):
    global combanulist
    if adminquery == "admindata":
        temp = {}
        tempparent = {}
        for i, j in db.items():
            for k, v in j.items():
                if k != "tfidf" and k != "vcr":
                    temp[k] = v
                    print(v)
            tempparent[i] = temp
            temp = {}
        return jsonify(tempparent)
    elif adminquery == "comunitydata":
        return jsonify({
            "history": dict(chat_history),
            "banned_users": combanulist
        })


@app.route("/banctl/<typeban>/<int:uid>", methods=["GET"])
def ban(typeban, uid):
    global combanulist
    if uid not in db:
        return jsonify({"error": "User not found"})

    if typeban == "comban":
        db[uid]["comban"] = 1
        combanulist.append(uid)
    elif typeban == "botban":
        db[uid]["botban"] = 1
    elif typeban == "unban":
        db[uid]["comban"] = 0
        db[uid]["botban"] = 0
    updt = db[uid]
    return jsonify({"success": "200"})


@app.route("/soilhealth/<int:uid>", methods=["GET"])
def soilhealth(uid):
    if uid not in db:
        return jsonify({
            "Nitrogen": "New User",
            "Phosphorus": "New User",
            "Potasium": "New User",
            "PH": "New User",
            "Soil Type": "New User"
        })
    return jsonify({
        "Nitrogen": str(db[uid]["nutri"][0]),
        "Phosphorus": str(db[uid]["nutri"][1]),
        "Potasium": str(db[uid]["nutri"][2]),
        "PH": str(db[uid]["nutri"][3]),
        "Soil Type": str(db[uid]["nutri"][4])
    })


#------------------------------------------------------------------------------
reportedMessages = []


@app.route("/setChatHistory/<city>/<uid>/<int:indexno>", methods=["POST"])
def setChatHistory(city, uid, indexno):
    global chat_history
    print(request.json)
    chat_history[city][int(indexno)] = request.json["message"]
    reportedMessages[request.json["rindex"]] = None
    return jsonify({"success": "200"})


@app.route("/reports", methods=["GET"])
def reports():
    return jsonify(reportedMessages)


@app.route("/alert/send/<int:uid>", methods=["GET"])
def alert(uid):
    global reportedMessages
    global switch

    print(request.json)
    global db
    if uid not in db:
        db[uid] = copy.deepcopy(page_format)
    if db[uid]["comban"] == 1:
        return jsonify([{
            "name": "Admin",
            "message": "You are banned for violating our Community Guidelines",
            "uid": 100
        }])
    if db[uid]["city"] == "":

        db[uid]["ip"] = request.headers.get("X-Forwarded-For").split(",")[0]
        geocode = httpx.get("http://ip-api.com/json/" + db[uid]["ip"])
        dat = geocode.json()
        db[uid]["city"] = dat["city"]
    data = request.json
    print(data)
    if db[uid]["city"] not in chat_history:
        chat_history[db[uid]["city"]] = []
    if data["message"] != "10001":
        switch = 3
        if "REDACT" in call_llm(data["message"]):
            reportedMessages.append([
                data["name"], data["message"], uid,
                len(chat_history[db[uid]["city"]]), db[uid]["city"]
            ])
            data[
                "message"] = f"Admin Message: Beware {data['name']}, You can be Banned !!! Your latest message was redacted for potential violation of our Community Guidelines. If you think this is a mistake, please contact us at 8799007739."
            chat_history[db[uid]["city"]].append(
                ["Admin", data["message"], 100])
        else:
            chat_history[db[uid]["city"]].append(
                [data["name"], data["message"], uid])
    ret = []
    print(db[uid]["city"])
    for idx, element in enumerate(chat_history[db[uid]["city"]]):
        ret.append({
            "name": element[0],
            "message": element[1],
            "uid": element[2]
        })
    return jsonify(ret)


#------------------------------------------------------------------------------


@app.route("/news", methods=["GET"])
def news():
    iteras = 0
    url = "https://krishijagran.com/news"
    response = requests.get(url)
    news = {}
    if response.status_code == 200:
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        headlines = soup.find_all("h2", class_="h", limit=10)

        news["Headline" + str(
            0
        )] = "You might be eligible for PM-KISAN scheme, providing ₹6,000 annually to eligible farmers."
        news["Link" + str(0)] = "https://pmkisan.gov.in/homenew.aspx"
        for idx, headline in enumerate(headlines, 3):
            iteras = iteras + 1
            title = headline.get_text(strip=True)
            try:
                for child in headline.children:
                    if child.name == "a":
                        news["Headline" + str(iteras)] = title
                        news["Link" + str(
                            iteras)] = "https://krishijagran.com" + child.get(
                                "href")
                        break
            except Exception:
                print("Error")
    else:
        print(f"Failed to fetch page. Status: {response.status_code}")
    return jsonify(news)


@app.route("/register", methods=["GET"])
def register():
    return jsonify({"uid": int(time.time() * 1000)})


#-------------- MAIN LOGIC -------------------
@app.route("/chat/<int:uid>", methods=["POST"])
def add_user(uid):

    global page_format
    global everyMod
    global llmcontext
    dicti = {}
    global db

    if uid not in db:
        db[uid] = copy.deepcopy(page_format)
    if db[uid]["botban"] == 1:
        dicti[
            "AIreply"] = "You are banned for violating our Community Guidelines"
        return jsonify(dicti)

#question for other models
    query_string = [
        "Enter Nitrogen Quantity", "Enter Phosphorus Quantity",
        "Enter Potassium Quantity", "Enter PH of your soil",
        "What is your soil type?", "What do you want to grow?"
    ]
    buttonsask = [[], [], [], [], ["Black", "Clayey", "Loamy", "Red", "Sandy"],
                  [
                      "Barley", "Cotton", "Groundnuts", "Maize", "Millet",
                      "Oil Seed", "Paddy", "Pulses", "Sugarcane", "Tobacco",
                      "Wheat", "Cofee", "Rajma", "Orange", "Annardana", "Rice",
                      "Watermellon"
                  ]]

    #------------------------------

    data = request.json
    print(data)

    if "message" not in data:
        return jsonify({"error": "Message is required"}), 400
    usrmess = data["message"]

    # MEMORY MEMORY MEMORY logic start
    if db[uid]["mode"] != 101 or db[uid]["mode"] != 102:
        if uid != 0:
            if db[uid]["vcr"] == None:  #if new user
                vectorizer = TfidfVectorizer()
                db[uid][
                    "llmcontext"] = "He is a new user greet him, say Namaste"
                db[uid]["corpus"].append(usrmess)
                db[uid]["tfidf"] = vectorizer.fit_transform(db[uid]["corpus"])
                db[uid]["vcr"] = vectorizer
            else:
                vectorizer = db[uid]["vcr"]
                qvec = vectorizer.transform([usrmess])
                sim = cosine_similarity(qvec, db[uid]["tfidf"]).flatten()
                print(sim)
                if max(sim) > 0.5:
                    sortsim = sim.tolist()
                    sortsim.sort(reverse=True)
                    db[uid][
                        "llmcontext"] = "This are some of the users previous message extract information as you see fit from it "
                    for index, score in enumerate(sortsim):
                        if index < 3:
                            if score > 0.5:
                                db[uid]["llmcontext"] = db[uid][
                                    "llmcontext"] + db[uid]["corpus"][
                                        sim.tolist().index(score)]

                db[uid]["corpus"].append(usrmess)
                db[uid]["tfidf"] = vectorizer.fit_transform(db[uid]["corpus"])
    print(len(db[uid]["corpus"]))

    #memory logic end

    #Routing logic start

    if db[uid]["mode"] == 102:
        try:
            if (str(db[uid]["nutri"][db[uid]["state"]]).isnumeric() ==
                    usrmess.isnumeric()):
                db[uid]["nutri"][db[uid]["state"]] = float(usrmess)
            else:
                dicti["AIreply"] = "Invalid Input, Please start again"
                db[uid]["state"] = page_format["state"]
                # db[uid]["nutri"] = copy.deepcopy(page_format["nutri"])
                db[uid]["state"] = page_format["state"]
                db[uid]["mode"] = page_format["mode"]
                db[uid]["model"] = page_format["model"]
                return jsonify(dicti)
        except Exception:

            db[uid]["nutri"][db[uid]["state"]] = usrmess
        db[uid]["state"] = db[uid]["state"] + 1
        if db[uid]["state"] == everyMod[db[uid]["model"]][1]:
            db[uid]["ip"] = request.headers.get("X-Forwarded-For").split(
                ",")[0]

            dicti["AIreply"] = str(predictmod(db[uid]))
            db[uid]["state"] = page_format["state"]
            #  db[uid]["nutri"] = copy.deepcopy(page_format["nutri"])
            db[uid]["state"] = page_format["state"]
            db[uid]["mode"] = page_format["mode"]
            db[uid]["model"] = page_format["model"]
        else:
            dicti["AIreply"] = query_string[db[uid]["state"]]
            for j, i in enumerate(buttonsask[db[uid]["state"]]):
                dicti["Button" + str(j)] = i
                print(i)
        return jsonify(dicti)
    if db[uid]["mode"] == 101 and usrmess == "OK":
        db[uid]["mode"] = 102
        dicti["AIreply"] = query_string[0]
        return jsonify(dicti)

#Routing logic end

#handling sms start
    global switch
    if uid == 0:
        switch = 1
#handling sms end

    llmcontext = db[uid]["llmcontext"]
    reply = call_llm(usrmess)  #Actual api call
    db[uid]["llmcontext"] = ""
    #reply for sms:
    if uid == 0:
        return jsonify({"AIreply": reply.replace("**", "")})


#reply for app:
    reply = reply.replace("<option number>:<Options>", "").split("\n")

    j = 0
    dicti["AIreply"] = reply[0].replace("Text:", "")
    for idx, i in enumerate(everyMod):
        if i[0] in dicti["AIreply"]:

            db[uid]["mode"] = 101
            db[uid]["model"] = idx
            dicti["AIreply"] = "Please Enter Data as asked"
            dicti["Button1"] = "OK"
            dicti["Button2"] = "Cancel"
            return jsonify(dicti)

    for i in reply:

        if j == 0:
            j = j + 1
            continue

        dicti["Button" + str(j)] = i
        j = j + 1
    dicti["AIreply"] = "" + dicti["AIreply"]
    return jsonify(dicti)

if __name__ == "__main__":
    app.run(debug=True, port=8080)
