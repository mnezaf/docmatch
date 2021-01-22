import os
import logging
from flask import Flask
from slack import WebClient
#from slackclient import SlackClient
from slackeventsapi import SlackEventAdapter
import ssl as ssl_lib
import certifi
from onboarding_tutorial import ChatBot
from pymetamap import MetaMap
import pickle
import pandas as pd
import numpy as np
from collections import defaultdict

symptoms=[]
cuis=[]
morecui=[]
METAMAP=<path to metamap18>
chatstep = 0
SLACK_SIGNING_SECRET = "37fe2ea7c749d46769a90290490ed3b0"
SLACK_BOT_TOKEN = "xoxb-936432166103-921844611250-PKClFsYspHR1sxQuHsPZU38x"

#dictionary for conversion of concept code to text
f = open(<path to MRCONSO.RRF>,'r', encoding='utf-8')
l = f.readline()
con2word = defaultdict(list)
for i in range(10000):
	while (l):
		words = l.strip().split("|")
		if words[1] == "ENG":
			con2word[words[0]].append(words[14])
		l = f.readline()

#dictionary for conversion of concept code to text
csp={}
nci={}
f = open("<path to MRDEF.RRF>,'r', encoding='utf-8')
l = f.readline()
for i in range(10000):
	while (l):
		words = l.strip().split("|")
		if words[4] == "NCI":
			nci[words[0]] = words[5]
		elif words[4] == "CSP":
			csp[words[0]] = words[5]
		l = f.readline()

        


# Initialize a Flask app to host the events adapter
app = Flask(__name__)
slack_events_adapter = SlackEventAdapter(SLACK_SIGNING_SECRET, "/slack/events", app)

# Initialize a Web API client
slack_web_client = WebClient(SLACK_BOT_TOKEN)
onboarding_tutorials_sent = {}
def predictSpecialist(cuilist):
	print(cuilist)
	f = open(<path to column_name.txt>,'r')
	column_name = f.read().splitlines()
	f.close()
	cuilist = list(set(cuilist).intersection(set(column_name)))
	if len(cuilist)==0:
		return (None,None)
	testdf = pd.DataFrame(np.zeros((1, len(column_name))))
	testdf.columns = column_name
	testdf[cuilist]=1
	logisticRegr = pickle.load(open(<path to specialist_classifier_logReg_UMLS>,'rb'))
	prob = logisticRegr.predict_proba(testdf)
	topprob = np.argsort(prob, axis=1)[0,][::-1][:3]
	return (logisticRegr.classes_[topprob],prob[0,topprob])
	
def findMoreSymptoms(cuilist):
	df = pd.read_csv(<path to discipline_symptoms_umls2.csv>,header=None)
	df.columns = ["specialist","disease","symptoms"]
	df = df[["disease","symptoms"]]
	dcand = df[df['symptoms'].isin(cuilist)]["disease"].unique()#find diseases with all the symptoms
	suggestions = df[df["disease"].isin(dcand)]["symptoms"].unique()
	return set(suggestions)-set(cuilist)


	
def start_onboarding(user_id: str, channel: str):
	# Create a new onboarding tutorial.
	onboarding_tutorial = ChatBot(channel)

	# Get the onboarding message payload
	message = onboarding_tutorial.get_message_onboarding()

	# Post the onboarding message in Slack
	response = slack_web_client.chat_postMessage(**message)

	# Capture the timestamp of the message we've just posted so
	# we can use it to update the message after a user
	# has completed an onboarding task.
	onboarding_tutorial.timestamp = response["ts"]

	# Store the message sent in onboarding_tutorials_sent
	if channel not in onboarding_tutorials_sent:
		onboarding_tutorials_sent[channel] = {}
	onboarding_tutorials_sent[channel][user_id] = onboarding_tutorial


def send_message(user_id: str, channel: str, txt: str):
	cb = ChatBot(channel)
	block = {
		"type": "section",
		"text": {
			"type": "mrkdwn",
			"text": txt,
		},
	}
	
	# Get the onboarding message payload
	message = cb.get_message_payload(block)

	# Post the onboarding message in Slack
	response = slack_web_client.chat_postMessage(**message)
	#slack_web_client.chat_postMessage("back pain")


def send_divider(user_id: str, channel: str):
	cb = ChatBot(channel)
	block = {"type": "divider"}
	# Get the onboarding message payload
	message = cb.get_message_payload(block)
	# Post the onboarding message in Slack
	response = slack_web_client.chat_postMessage(**message)

# ================ Team Join Event =============== #
# When the user first joins a team, the type of the event will be 'team_join'.
# Here we'll link the onboarding_message callback to the 'team_join' event.
@slack_events_adapter.on("team_join")
def onboarding_message(payload):
	"""Create and send an onboarding welcome message to new users. Save the
	time stamp of this message so we can update this message in the future.
	"""
	event = payload.get("event", {})

	# Get the id of the Slack user associated with the incoming event
	user_id = event.get("user", {}).get("id")

	# Open a DM with the new user.
	response = slack_web_client.im_open(user_id)
	channel = response["channel"]["id"]

	# Post the onboarding message.
	start_onboarding(user_id, channel)


# ============= Reaction Added Events ============= #
# When a users adds an emoji reaction to the onboarding message,
# the type of the event will be 'reaction_added'.
# Here we'll link the update_emoji callback to the 'reaction_added' event.
@slack_events_adapter.on("reaction_added")
def update_emoji(payload):
	"""Update the onboarding welcome message after receiving a "reaction_added"
	event from Slack. Update timestamp for welcome message as well.
	"""
	event = payload.get("event", {})

	channel_id = event.get("item", {}).get("channel")
	user_id = event.get("user")

	if channel_id not in onboarding_tutorials_sent:
		return

	# Get the original tutorial sent.
	onboarding_tutorial = onboarding_tutorials_sent[channel_id][user_id]

	# Mark the reaction task as completed.
	onboarding_tutorial.reaction_task_completed = True

	# Get the new message payload
	message = onboarding_tutorial.get_message_payload()

	# Post the updated message in Slack
	updated_message = slack_web_client.chat_update(**message)

	# Update the timestamp saved on the onboarding tutorial object
	onboarding_tutorial.timestamp = updated_message["ts"]


# =============== Pin Added Events ================ #
# When a users pins a message the type of the event will be 'pin_added'.
# Here we'll link the update_pin callback to the 'reaction_added' event.
@slack_events_adapter.on("pin_added")
def update_pin(payload):
	"""Update the onboarding welcome message after receiving a "pin_added"
	event from Slack. Update timestamp for welcome message as well.
	"""
	event = payload.get("event", {})

	channel_id = event.get("channel_id")
	user_id = event.get("user")

	# Get the original tutorial sent.
	onboarding_tutorial = onboarding_tutorials_sent[channel_id][user_id]

	# Mark the pin task as completed.
	onboarding_tutorial.pin_task_completed = True

	# Get the new message payload
	message = onboarding_tutorial.get_message_payload()

	# Post the updated message in Slack
	updated_message = slack_web_client.chat_update(**message)

	# Update the timestamp saved on the onboarding tutorial object
	onboarding_tutorial.timestamp = updated_message["ts"]


# ============== Message Events ============= #
# When a user sends a DM, the event type will be 'message'.
# Here we'll link the message callback to the 'message' event.
@slack_events_adapter.on("message")
def message(payload):
	"""Display the onboarding welcome message after receiving a message
	that contains "start".
	"""
	event = payload.get("event", {})

	channel_id = event.get("channel")
	user_id = event.get("user")
	text = event.get("text")
	if text.find("displayed.")!=-1 : return
	print(text)
	global chatstep
	global concepts
	global cuis
	global morecui
	print(chatstep)
	#---Onboarding
	if chatstep==0 and text.find("This content can't be displayed.")==-1:
		if text and text.find("This content can't be displayed.")==-1:
			chatstep = chatstep+1
			return start_onboarding(user_id, channel_id)

	elif chatstep==1: #getting the symptoms
		if text and text.lower() != "done" and text.find("This content can't be displayed.")==-1:
			symptoms.append(text)
		elif text and text.lower() == "done":
			chatstep+=1
			print(chatstep)
			print(text)
			#IMPROTANT: metamap services should be started before running the following lines
			# "wsdserverctl start" and "skrmedpostctl start"
			mm = MetaMap.get_instance(METAMAP)
			concepts, error = mm.extract_concepts(symptoms)
			text=None
			#keep only semantic type of "sign or symptom"
			sos = []
			for con in concepts:
				if con.semtypes=="[sosy]":
					sos.append(con)
					cuis.append(con.cui)
	
			send_message(user_id, channel_id,"Thanks! Let's check if I understand you correctly!")
			send_message(user_id, channel_id,"Do you have the following symptoms?\n")
			#send_divider(user_id, channel_id)
			#confirm symptoms
			txt=""
			for con in sos:
				txt += "*{}*\n".format(con.preferred_name)
			send_message(user_id, channel_id,txt)
			send_divider(user_id, channel_id)
			send_message(user_id, channel_id,"Please enter yes/no")
			symptoms.clear()
			return
			#open model
		
	elif chatstep==2: # confirmation of symptoms
		if text and text.lower() == "yes"  and text.find("This content can't be displayed.")==-1:
			chatstep = chatstep+1
			morecui = list(findMoreSymptoms(cuis))
			if len(morecui)!=0:
				msg = "I found some related sypmtoms. If you have any of the following symptoms please enter the numbers separated by comma. Otherwise please enter \'no\'"
				send_message(user_id,channel_id,msg)
				send_divider(user_id,channel_id)
				txt=""
				for i in range(len(morecui)):
					con = morecui[i]
					#txt += "{}-{} , ".format(i+1,con2word[con][0])
					try:
						txt += "{}- {} : {} \n".format(i+1,con2word[con][0],nci[con])
					except:
						try:
							txt += "{}- {} : {} \n".format(i+1,con2word[con][0],csp[con])
						except:
							txt += "{}- {} \n".format(i+1,con2word[con][0])
						
				send_message(user_id,channel_id,txt)
				send_divider(user_id,channel_id)
				return
			else:#no more symptoms found
				spec,prob = predictSpecialist(cuis)
				if (spec):
					send_message(user_id,channel_id,"Based on my analysis you should visit the following specialist:")
					txt=""
					for i in len(spec):
						txt += "{} (probability = )\n-------------------------------\n".format(spec[i],prob[i])
					send_message(user_id,channel_id,txt)
				else:
					send_message(user_id,channel_id,"I was not able to find any specialist based on your symptoms so please visit a general practitioner for more guidance.")
				chatstep=4
				return
		elif text and text.lower() == "no":
			send_message(user_id,channel_id,"*Please describe your signs and symptoms. When finished please type \'done\'.*")	
			chatstep = chatstep-1
		text=None	
		return
	
	elif chatstep==3:
		if text.find("This content can't be displayed.")!=-1: return
		chatstep=chatstep+1
		print(text)
		if text and text.lower()!="no" and text.find("displayed")==-1:
			try:
				morenum = text.split(",")
				morenum = [int(x) for x in morenum]
				print(morenum)
				print(morecui)
				for i in morenum:
					cuis.append(morecui[i-1])
			except:
				chatstep = chatstep-1
				send_message(user_id,channel_id,"Sorry! I did not understand! If you have any of the above symptoms please enter the numbers separated by comma. Otherwise, please enter No")
				return
		spec,prob = predictSpecialist(cuis)
		if (len(spec)>0):
			send_message(user_id,channel_id,"Based on my analysis you should visit the following specialist:")
			for i in range(len(spec)):
				txt = "*{} (probability = {:.3f} )*".format(con2word[spec[i]][0],prob[i])
				#txt = "*{} (probability = {:.2f} )*".format(spec[i],prob[i])
				send_message(user_id,channel_id,txt)
				send_divider(user_id,channel_id)
		else:
			send_message(user_id,channel_id,"Sorry! I was not able to find any specialist based on your symptoms so please visit a general practitioner for more guidence.")
			return
		send_message(user_id,channel_id,"Thanks for using Docmatch :wave:")
		return
	#elif chatstep==4 and text.find("displayed")==-1:
		#chatstep+=1
		#if text and text.lower()=="yes" and text.find("This content can't be displayed.")==-1:
			#chatstep=1
			#return start_onboarding(user_id, channel_id)
		#elif text and text.lower().find("no")!=-1 and text.find("This content can't be displayed.")==-1:
			#return send_message(user_id,channel_id," Have a nice time :wave:")
	return
#MEtamap start:
# ./bin/wsdserverctl start
#./bin/skrmedpostctl start

if __name__ == "__main__":
	logger = logging.getLogger()
	logger.setLevel(logging.DEBUG)
	logger.addHandler(logging.StreamHandler())
	ssl_context = ssl_lib.create_default_context(cafile=certifi.where())
	app.run(port=3000)
