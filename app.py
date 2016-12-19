#!/usr/bin/env python

import urllib
import json
import os

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
	req = request.get_json(silent=True, force=True)

	print("Request:")
	print(json.dumps(req, indent=4))

	res = processRequest(req)

	res = json.dumps(res, indent=4)
	# print(res)
	r = make_response(res)
	r.headers['Content-Type'] = 'application/json'
	return r


def processRequest(req):
	if req.get("result").get("action") == "yahooWeatherForecast":
		baseurl = "https://query.yahooapis.com/v1/public/yql?"
		yql_query = makeYqlQuery(req)
		if yql_query is None:
			return {}
		yql_url = baseurl + urllib.urlencode({'q': yql_query}) + "&format=json"
	
		print("yql_url:")
		print(yql_url)
	
		result = urllib.urlopen(yql_url).read()
		data = json.loads(result)
		res = makeYqlWebhookResult(data)
		return res

	elif req.get("result").get("action") == "shopping.search":
		baseurl = "http://search.mobile.walmart.com/v1/browse/search?assetProtocol=normal&itemSource=All&sortBy=BESTSELLERS&spelling=false&"
		wm_query = makeWalmartQuery(req)
		if wm_query is None:
			return {}
		wm_url = baseurl + urllib.urlencode({'query': wm_query})
	
		print("wm_url:")
		print(wm_url)
	
		result = urllib.urlopen(wm_url).read()
		data = json.loads(result)
		res = makeWmWebhookResult(data)
		return res
		
	else:
		return {}


def makeYqlQuery(req):
	result = req.get("result")
	parameters = result.get("parameters")
	city = parameters.get("geo-city")
	if city is None:
		return None

	return "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "')"


def makeWalmartQuery(req):
	result = req.get("result")
	parameters = result.get("parameters")
	query = parameters.get("q")
	if query is None:
		return None

	return query


def makeYqlWebhookResult(data):
	query = data.get('query')
	if query is None:
		return {}

	result = query.get('results')
	if result is None:
		return {}

	channel = result.get('channel')
	if channel is None:
		return {}

	item = channel.get('item')
	location = channel.get('location')
	units = channel.get('units')
	if (location is None) or (item is None) or (units is None):
		return {}

	condition = item.get('condition')
	if condition is None:
		return {}

	# print(json.dumps(item, indent=4))

	speech = "Today in " + location.get('city') + ": " + condition.get('text') + \
			 ", the temperature is " + condition.get('temp') + " " + units.get('temperature')

	print("Response:")
	print(speech)

	return {
		"speech": speech,
		"displayText": speech,
		# "data": data,
		# "contextOut": [],
		"source": "apiai-weather-webhook-sample-ga"
	}


def makeWmWebhookResult(data):
	item = data.get('item')[0]
	if item is None:
		return {}

	name = item.get('name')
	if name is None:
		return {}

	price = item.get('price')
	if price is None:
		return {}

	# print(json.dumps(item, indent=4))

	speech = "I found " + item.get('name') + " at Walmart for " + item.get('price')

	print("Response:")
	print(speech)

	return {
		"speech": speech,
		"displayText": speech,
		# "data": data,
		# "contextOut": [],
		"source": "apiai-weather-webhook-sample-ga"
	}


if __name__ == '__main__':
	port = int(os.getenv('PORT', 5000))

	print "Starting app on port %d" % port

	app.run(debug=False, port=port, host='0.0.0.0')
