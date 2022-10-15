# coding: utf-8
import requests
import constants
import json

params = {
  'access_key': constants.weatherstack_access_key,
  'query': '77070',
  'units': 'f'
}

api_result = requests.get('http://api.weatherstack.com/forecast', params)
print(json.dumps(api_result.json(), indent=2))

api_response = api_result.json()

print(u'Current temperature in %s is %d°F' % (api_response['location']['name'], api_response['current']['temperature']))