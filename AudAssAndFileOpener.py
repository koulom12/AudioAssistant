from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import time
import pytz
import pyttsx3
import speech_recognition as sr
import subprocess



SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
MONTHS = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
EXTENSIONS = ["nd", "rd", "th", "st"]

def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    
def get_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
        said =""

    try :
        said = r.recognize_google(audio)
        print(said)
    except Exception as e:
        print("Exception: "+ str(e))

    return said.lower()

def authenticate_google():
    creds = None
    
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service

  # Call the Calendar API
def get_events(day,service):
    date = datetime.datetime.combine(day,datetime.datetime.min.time())
    end = datetime.datetime.combine(day,datetime.datetime.max.time())
    utc = pytz.UTC
    date=date.astimezone(utc)
    end = end.astimezone(utc)
    
    events_result = service.events().list(calendarId='primary', timeMin=date.isoformat(),timeMax=end.isoformat(), singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        speak('No upcoming events found.')
    else:
        speak(f'You have {len(events)} events on this day')
        
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])
            start_time =  str(start.split("T")[1].split("+")[0])
            if int(start_time.split(":")[0])<12:
                start_time = str(start_time.split(":")[0])+str(start_time.split(":")[1])
                start_time= start_time+"am"
            else:
                start_time = str(int(start_time.split(":")[0])-12)+str(start_time.split(":")[1])
                start_time= start_time+"pm"
            speak(event["summary"]+"at"+start_time)



def get_date(text):
    text= text.lower()
    today = datetime.date.today()
    if text.count("today")>0:
        return today
    
    if text.count("tomorrow")>0:
        tomorrow= today+ datetime.timedelta(days=1)
        return tomorrow
    day = -1
    day_of_week =-1
    month = -1
    year = today.year
    
    for word in text.split():
        if word in MONTHS:
            month = MONTHS.index(word)+1
        elif word in DAYS:
            day_of_week = DAYS.index(word)
        elif word.isdigit():
            day = int(word)
        else:
            for ext in EXTENSIONS:
                found = word.find(ext)
                if found>0:
                    try:
                        day = int(word[:found])
                    except:
                        pass
    
    if month < today.month and month!=-1:
        year+=1

    if month==-1 and day!=-1:
        if day<today.day:
            month+=1
        else:
            month = today.month

    if month == -1 and day == -1 and day_of_week!=-1:
        current_day_of_week = today.weekday()
        dif = day_of_week - current_day_of_week

        if dif<0:
            dif+=7
            if text.count("next")>=1:
                dif+=7
        elif dif>=0:
            if text.count("next")>=1:
                dif+=7

        return today+ datetime.timedelta(dif)
    
    if month ==-1 or day==-1:
        return None
    return datetime.date(month = month, day = day, year = year)

def note(text):
    date = datetime.datetime.now()
    filename = str(date).replace(':','-') + "-note.txt"
    with open(filename,"w") as f:
        f.write(text)
    
    subprocess.Popen(["notepad.exe",filename])

wake = "hey homie"
service = authenticate_google()
print("Start")

while True:
    print("Listening")
    text = get_audio()

    if text.count(wake)>0:
        speak("I am ready!")
        text = get_audio()
        
        CALENDAR_STRS = ["do i have any plans", "am i busy", "what do i have"]
        for phrase in CALENDAR_STRS:
            if phrase in text:
                date = get_date(text)
                if date:
                    get_events(date,service)
                else:
                    speak("Please Try Again")

        NOTEPAD_STRS = ["make a note","write it down","save for me"]
        for phrase in NOTEPAD_STRS:
            if phrase in text:
                speak("What do you want to note down")
                notepad_text = get_audio()
                note(notepad_text)
                speak("I have made a note of that.")


        






