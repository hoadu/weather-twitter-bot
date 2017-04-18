import tweepy
import time
import requests
import json
import datetime
import string
import threading
from credentials import * #Imports personal information/keys that should be hidden from a credentials.py

#API temperature data response is in Kelvin, convert Kelvin temperature to Fahrenheit
def convert_temp(kelvin_temp):
    fahrenheit_temp = 9/5*(kelvin_temp - 273) + 32
    return fahrenheit_temp

#Formats forecast time into easily readable words
def format_forecast_time(forecast_time):
    date = forecast_time.split()[0]
    if int(date.split('-')[1]) == 1:
        date_in_words = 'January ' + date.split('-')[2] + ', ' + date.split('-')[0] + ' ' + forecast_time.split()[1]
    elif int(date.split('-')[1]) == 2:
        date_in_words = 'February ' + date.split('-')[2] + ', ' + date.split('-')[0] + ' ' + forecast_time.split()[1]
    elif int(date.split('-')[1]) == 3:
        date_in_words = 'March ' + date.split('-')[2] + ', ' + date.split('-')[0] + ' ' + forecast_time.split()[1]
    elif int(date.split('-')[1]) == 4:
        date_in_words = 'April ' + date.split('-')[2] + ', ' + date.split('-')[0] + ' ' + forecast_time.split()[1]
    elif int(date.split('-')[1]) == 5:
        date_in_words = 'May ' + date.split('-')[2] + ', ' + date.split('-')[0] + ' ' + forecast_time.split()[1]
    elif int(date.split('-')[1]) == 6:
        date_in_words = 'June ' + date.split('-')[2] + ', ' + date.split('-')[0] + ' ' + forecast_time.split()[1]
    elif int(date.split('-')[1]) == 7:
        date_in_words = 'July ' + date.split('-')[2] + ', ' + date.split('-')[0] + ' ' + forecast_time.split()[1]
    elif int(date.split('-')[1]) == 8:
        date_in_words = 'August ' + date.split('-')[2] + ', ' + date.split('-')[0] + ' ' + forecast_time.split()[1]
    elif int(date.split('-')[1]) == 9:
        date_in_words = 'September ' + date.split('-')[2] + ', ' + date.split('-')[0] + ' ' + forecast_time.split()[1]
    elif int(date.split('-')[1]) == 10:
        date_in_words = 'October ' + date.split('-')[2] + ', ' + date.split('-')[0] + ' ' + forecast_time.split()[1]
    elif int(date.split('-')[1]) == 11:
        date_in_words = 'November ' + date.split('-')[2] + ', ' + date.split('-')[0] + ' ' + forecast_time.split()[1]
    elif int(date.split('-')[1]) == 12:
        date_in_words = 'December ' + date.split('-')[2] + ', ' + date.split('-')[0] + ' ' + forecast_time.split()[1]
    return date_in_words

#Figures out what advice to put in the tweet
def get_advice(weather_category):
    rain = {'Thunderstorm', 'Drizzle', 'Rain'}
    if weather_category in rain:
        advice = 'Bring an umbrella!'
    elif weather_category == 'Snow':
        advice = 'Wear boots!'
    elif weather_category == 'Atmosphere':
        advice = 'Be careful driving!'
    elif weather_category == 'Clear':
        advice = 'Bring water!'
    elif weather_category == 'Clouds':
        advice = 'Wear a jacket!'
    elif weather_category == 'Extreme':
        advice = '⚠Extreme weather alert⚠'
    elif weather_category == 'Additional':
        advice = 'It\'s windy out there!'
    return advice

def get_forecast_message():
    #Calling openweathermap API for the weather forecast data in JSON format restricted to 24 hours in the future, default location is East Brunswick
    forecast_payload = {'q': 'East Brunswick', 'cnt': '8', 'appid': apikey, 'type': 'accurate'}
    forecast_request = requests.get('http://api.openweathermap.org/data/2.5/forecast?', params = forecast_payload)
    forecast = json.loads(forecast_request.text)

    #Gets necessary weather forecast data for tweet from API request
    city = forecast['city']['name']
    country = forecast['country']
    forecast_unix_time = forecast['list'][4]['dt']
    forecast_time = datetime.datetime.fromtimestamp(int(forecast_unix_time)).strftime('%Y-%m-%d %H:%M:%S') #Converting from Unix time to slightly more readable format
    formatted_forecast_time = format_forecast_time(forecast_time)
    weather = string.capwords(forecast['list'][4]['weather'][0]['description'])
    high_temp = int(convert_temp(forecast['list'][4]['main']['temp_max']))
    low_temp = int(convert_temp(forecast['list'][4]['main']['temp_min']))
    average_temp = float((high_temp + low_temp) / 2)
    weather_category = forecast['list'][4]['weather'][0]['main']
    advice = get_advice(weather_category)

    #Concatenates all the weather data into a forecast message
    message = '{} {}, {}\n{}\nHigh: {}°F\nLow: {}°F\nAvg: {}°F\n{}\nNo Tweet=Unchanged'.format(city, country, formatted_forecast_time, weather, high_temp, low_temp, average_temp, advice)
    return message

#Allows weather bot to check if anyone told it to stop every 30 seconds while updating its forecast using threading
class stopThread(threading.Thread):
    def __init__(self, stop):
        threading.Thread.__init__(self)
        self.stop = stop
        self.daemon = True
    def run(self):
        print("Starting " + self.name)
        stop = False
        while True:
            mentions = api.mentions_timeline(count = 1)
            for mention in mentions:
                tweet_text = mention.text
                tweet_text = tweet_text.replace(bot_twitter_handle, '')
            tweet_text = tweet_text.upper().replace(' ', '')#Cleaning @mention tweet text
            if tweet_text == 'STOP':
                self.stop = True
            print('Told to stop? ' + str(self.stop)+ ' ' + str(datetime.datetime.now()))
            time.sleep(30)

#Gets the bot to tweet the forecast
def tweet():
    try: #Handles exceptions where Tweepy gives some kind of error while trying to tweet
        tweet = get_forecast_message() #Call function to get the weather forecast message to tweet
        print(tweet) #Printing text in tweet for debugging
        print('Attempt time: ' + str(datetime.datetime.now())) #Time the bot attempted to tweet
        api.update_status(tweet) #Tweets forecast
    except tweepy.TweepError as e:
        print(e.reason)

#Access twitter account to be able to tweet from it
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

# Create new thread
check_for_stop = stopThread(False)

# Start the thread
check_for_stop.start()
twitter_user = ''
count = 0
tweet()
#Bot will continue tweeting updated forecasts every 5 minutes indefinitely until someone tweets at it to stop
while True:
    time.sleep(30)
    if check_for_stop.stop: #Checks if the stopThread has found someone telling the bot to stop
        break #If someone told bot to stop it shuts down
    count += 1
    if count == 10:
        tweet() #Attempts to tweet every 5 minutes
        count = 0

#Comes here when bot has been told to stop tweeting forecasts
mentions = api.mentions_timeline(count=1) #Gets most recent @mention of weather forecast bot from timeline

for mention in mentions:
    twitter_user = '@' + mention.user.screen_name #Gets the twitter handle of the user that told bot to stop
api.update_status(twitter_user + ' killed the weather bot :(')
