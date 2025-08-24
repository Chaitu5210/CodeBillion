import requests
import config

url = "https://api.upstox.com/v2/login/authorization/dialog"
params = {
    "client_id": config.api_key,
    "redirect_uri": config.redirect_url,
    "state": config.state
}
headers = {
    "accept": "application/json"
}

response = requests.get(url, headers=headers, params=params)
print(response.text)