import streamlit as st
import time
import requests
response_chatbotdata={}
response_communitydata={}

    
def fetchdata():
    global response_chatbotdata
    global response_communitydata
    global reportedusers
    response_chatbotdata=requests.get("https://e299fb02-a23b-4071-8f1c-cd6939767713-00-uqfu9h7yuvn8.sisko.replit.dev:3001/admindata").json()
    st.session_state["chatbot"]=response_chatbotdata
    response_communitydata=requests.get("https://e299fb02-a23b-4071-8f1c-cd6939767713-00-uqfu9h7yuvn8.sisko.replit.dev:3001/comunitydata").json()
    st.session_state["commdata"]=response_communitydata
    reportedusers=requests.get("https://e299fb02-a23b-4071-8f1c-cd6939767713-00-uqfu9h7yuvn8.sisko.replit.dev:3001/reports").json()
    st.session_state["report"]=reportedusers
def start():
    st.set_page_config(page_title="Admin Portal", layout="wide")
    page_element="""
    <style>
    [data-testid="stHeader"]{
    display:none;
}
[data-testid=stSidebarHeader]{
display:none;
}
    [data-testid="stAppViewContainer"]{
      background-image: url("https://videos.openai.com/vg-assets/assets%2Ftask_01k525edm2eypr1yyk9cxm72tc%2F1757788299_img_0.webp?st=2025-09-13T17%3A16%3A14Z&se=2025-09-19T18%3A16%3A14Z&sks=b&skt=2025-09-13T17%3A16%3A14Z&ske=2025-09-19T18%3A16%3A14Z&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skoid=5e5fc900-07cf-43e7-ab5b-314c0d877bb0&skv=2019-02-02&sv=2018-11-09&sr=b&sp=r&spr=https%2Chttp&sig=x54A8FwHujs2ydWtmPJorAOMv23hiaH6y%2FCqGv5FxBs%3D&az=oaivgprodscus");
      background-size: cover;
background-repeat:no-repeat;

      
    }
#welcome{
padding-top:150px;
color:white;
font-weight:700;
font-size:100px;
-webkit-text-stroke: 3px black; 
}
#to-green-revolution-2-0{
color:white;

font-size:60px;
-webkit-text-stroke: 1px black; 
}
    </style>
    """

    st.markdown(page_element, unsafe_allow_html=True)
    st.title("WELCOME")
    st.subheader("to Green Revolution 2.0")
    
    
  #  st.image("back.png")
    with st.sidebar:
        st.title("Admin Panel")
        st.image("background.png")
        st.divider()
        st.header("Moderation Tools")
        
        st.button("Unban Users",key=str(time.time()))
        
           
        
        
        st.button("Reported Messages",key=str(time.time()),on_click=reportedusers23)
        st.button("View Chatbot Activity",on_click=chatbotban,key=str(time.time()))
        st.button("View Community Chats",on_click=comchat,key=str(time.time())) 
    st.markdown("""
<style>
    [data-testid=stSidebar] {
        background-color: #52a447;
    }
</style>
""", unsafe_allow_html=True)
    st.stop()


def goback(p):
    st.set_page_config(page_title="Admin Portal", layout="wide")
    
    st.header("Admin Portal")
    with st.sidebar:
        st.title("Admin Panel")
        st.image("background.png")
        st.header("-----------------")
       
        st.button("Go Back",on_click=st.rerun,key=str(time.time()))
    st.markdown(f"""
<style>
#welcome,#to-green-revolution-2-0{{
color:white;}}
    [data-testid=stSidebar] {{
        background-color: #52a447;
    }}

    [data-testid="stHeader"]{{
    display:none;
}}
[data-testid=stSidebarHeader]{{
display:none;
}}
    [data-testid="stAppViewContainer"]{{
      background-image: url("{p}");
      background-size: contain;
        background-repeat:no-repeat;
background-position: right;
background-attachment: fixed;
        
    }}

}}
    </style>
""", unsafe_allow_html=True)
def comban(p,r):
    
    resp=requests.get("https://e299fb02-a23b-4071-8f1c-cd6939767713-00-uqfu9h7yuvn8.sisko.replit.dev:3001/banctl/comban/"+str(p)).json()
    if "success" in resp:
        st.warning("Status: User "+str(p)+" Banned")
        time.sleep(3)
    if r!=901:        
        comchat2(r)
    else:
        reportedusers23()
def comchat2(p):
    goback("https://videos.openai.com/vg-assets/assets%2Ftask_01k52b2bddezeschgq19vp5cvk%2F1757794197_img_0.webp?st=2025-09-13T19%3A07%3A39Z&se=2025-09-19T20%3A07%3A39Z&sks=b&skt=2025-09-13T19%3A07%3A39Z&ske=2025-09-19T20%3A07%3A39Z&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skoid=cfbc986b-d2bc-4088-8b71-4f962129715b&skv=2019-02-02&sv=2018-11-09&sr=b&sp=r&spr=https%2Chttp&sig=u8EZjoSKCsmYgLuqYTFEYi98yzmaSv%2BagTAPxwK0XKM%3D&az=oaivgprodscus")
    st.header("Messages in "+p+" community:");
    for i in st.session_state["commdata"][p]:
        with st.chat_message(i[0]):         
            st.write("**"+i[0]+": "+i[1]+"**")
            st.button("Ban User",key=str(time.time()),on_click=comban,args=(i[2],p,))
    st.stop() 

def comchat():
    global response_communitydata
    goback("https://videos.openai.com/vg-assets/assets%2Ftask_01k52b2bddezeschgq19vp5cvk%2F1757794197_img_0.webp?st=2025-09-13T19%3A07%3A39Z&se=2025-09-19T20%3A07%3A39Z&sks=b&skt=2025-09-13T19%3A07%3A39Z&ske=2025-09-19T20%3A07%3A39Z&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skoid=cfbc986b-d2bc-4088-8b71-4f962129715b&skv=2019-02-02&sv=2018-11-09&sr=b&sp=r&spr=https%2Chttp&sig=u8EZjoSKCsmYgLuqYTFEYi98yzmaSv%2BagTAPxwK0XKM%3D&az=oaivgprodscus")
    st.subheader("Select City");
    print("Got the following data")
    print(response_communitydata)
    fetchdata()
    for i in response_communitydata:
        st.button(i,on_click=comchat2,args=(i,),key=str(time.time()));
    st.stop()
#---------------------------isolate
def banbot(p):
    resp=requests.get("https://e299fb02-a23b-4071-8f1c-cd6939767713-00-uqfu9h7yuvn8.sisko.replit.dev:3001/banctl/botban/"+str(p)).json()
    if "success" in resp:
        st.warning("Status: User "+str(p)+" Banned")
        time.sleep(3)
    chatbotban()

def chatbotban():
    global response_chatbotdata
    goback("https://videos.openai.com/vg-assets/assets%2Ftask_01k52eh09xfaqaap1s5f0czwdm%2F1757797746_img_0.webp?st=2025-09-13T20%3A00%3A36Z&se=2025-09-19T21%3A00%3A36Z&sks=b&skt=2025-09-13T20%3A00%3A36Z&ske=2025-09-19T21%3A00%3A36Z&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skoid=cfbc986b-d2bc-4088-8b71-4f962129715b&skv=2019-02-02&sv=2018-11-09&sr=b&sp=r&spr=https%2Chttp&sig=iM1fHN7pr63Zd1Co%2BdxVNb1LGaaFhewi%2Fl7ItH%2Fs%2Bck%3D&az=oaivgprodscus")    
    fetchdata()
    for i,j in response_chatbotdata.items():
        print("Got the follwing data")
        print(j["corpus"])
        st.info("User_"+str(i))
        for ij in j["corpus"]:        
            st.write(ij.replace("weather","").replace("news",""))
        st.button("Ban User",key=str(time.time()),on_click=banbot,args=(i,))
        st.divider()
        
    st.stop()                     


#-------------------------------isolate end
def release(name,mess,uid,index,city):
    global response_communitydata
    requests.post("https://e299fb02-a23b-4071-8f1c-cd6939767713-00-uqfu9h7yuvn8.sisko.replit.dev:3001/setChatHistory/"+str(city)+"/"+str(uid)+"/"+str(index),json={"message":[name,mess,uid]})
    time.sleep(3)
    reportedusers23()
    
    
def reportedusers23():
    global reportedusers;
    goback("https://videos.openai.com/vg-assets/assets%2Ftask_01k52ejqgmfhhsmn763ph280zm%2F1757797846_img_1.webp?st=2025-09-13T20%3A03%3A23Z&se=2025-09-19T21%3A03%3A23Z&sks=b&skt=2025-09-13T20%3A03%3A23Z&ske=2025-09-19T21%3A03%3A23Z&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skoid=cfbc986b-d2bc-4088-8b71-4f962129715b&skv=2019-02-02&sv=2018-11-09&sr=b&sp=r&spr=https%2Chttp&sig=JDTEpgpFB00hSAw%2BuT8nrv3Q%2BCal%2BK7VTvtJgr5bmr0%3D&az=oaivgprodscus")
    st.subheader("Reported Messages")
    fetchdata()
    for entry in reportedusers:
        with st.chat_message(entry[0]):
            st.write(entry[0]+": "+entry[1])
            st.button("Ban User",key=str(time.time()),on_click=comban,args=(entry[2],901,))
            st.button("Release Message",key=str(time.time()),on_click=release,args=(entry[0],entry[1],entry[2],entry[3],entry[4],))
    st.stop()



start()





