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

apiswitch = 0
llmcontext = ""
page_format = {
    "mode": 0,
    "model": 0,
    "nutri": [0, 0, 0, 0, ""],
    "state": 0,
    "ip": "",
    "tfidf": None,
    "corpus": ["weather", "news"],
    "vcr": None,
    "llmcontext": "",
    "city": ""
}
switch = 0
model1 = joblib.load("crop_prediction.pkl")
df = pd.read_csv("state_month_avg_rainfall.csv")
df = df.set_index("state_name")
db = {}
everyMod = [["REDIRECT_TO_MODEL1", 4], ["REDIRECT_TO_MODEL2", 5]]
load_dotenv()
OPENAI_API_KEY = [os.getenv("OPENAI_API_KEY"), os.getenv("OPENAI_API_KEY1")]

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # multilingual model
chat_history = {}


def predictmod(dbuid):
    if dbuid["model"] == 0:
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
        return model1.predict(
            [[
                dbuid["nutri"][0], dbuid["nutri"][1], dbuid["nutri"][2],
                dbuid["nutri"][3], rainfall, humidity
            ]]
        )[0] + " is the best crop supporting your soil" or "No crop is suitable for your soil"
    if dbuid["model"] == 1:
        return "Thank You for using our service"


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
or if you feel regadless of language if farmer wants to plant a specific crop
then write only this REDIRECT_TO_MODEL2 only and nothing else
"""
    system_prompt_sms = '''
    You are an agriculture related sms bot. Resolve the query .Reply in the same language as that of user Default Language:English .

    '''
    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY[apiswitch%2]}",
            "Content-Type": "application/json"
        }
        print(OPENAI_API_KEY[apiswitch % 2])
        if switch == 1:
            system_prompt = system_prompt_sms

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

        r = httpx.post("https://api.openai.com/v1/chat/completions",
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


#------------------------------------------------------------------------------
@app.route("/alert/send/<int:uid>", methods=["GET"])
def alert(uid):
    global db
    if uid not in db:
        db[uid] = copy.deepcopy(page_format)
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
        )] = "Code Avengers also provide SMS based query service for basic phones/non smartphones. Try now by sending a sms to 8799007739."
        news["Link" + str(0)] = "sms:8799007739"
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

#question for other models
    query_string = [
        "Enter Nitrogen Quantity", "Enter Phosphorus Quantity",
        "Enter Potassium Quantity", "Enter PH of your soil",
        "What do you want to grow?"
    ]
    #------------------------------

    data = request.json
    print(data)

    if "message" not in data:
        return jsonify({"error": "Message is required"}), 400
    usrmess = data["message"]

    # MEMORY MEMORY MEMORY logic start
    if db[uid]["mode"] != 101 or db[uid]["mode"] != 102:
        if uid != 0:
            if len(db[uid]["corpus"]) == 2:  #if new user
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

            db[uid]["nutri"][db[uid]["state"]] = float(usrmess)
        except Exception:

            db[uid]["nutri"][db[uid]["state"]] = usrmess
        db[uid]["state"] = db[uid]["state"] + 1
        if db[uid]["state"] == everyMod[db[uid]["model"]][1]:
            db[uid]["ip"] = request.headers.get("X-Forwarded-For").split(
                ",")[0]

            dicti["AIreply"] = str(predictmod(db[uid]))
            db[uid]["state"] = page_format["state"]
            db[uid]["nutri"] = copy.deepcopy(page_format["nutri"])
            db[uid]["state"] = page_format["state"]
            db[uid]["mode"] = page_format["mode"]
            db[uid]["model"] = page_format["model"]
        else:
            dicti["AIreply"] = query_string[db[uid]["state"]]
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
        if dicti["AIreply"] == i[0]:

            db[uid]["mode"] = 101
            db[uid]["model"] = 0
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

