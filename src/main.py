import os
from dotenv import load_dotenv
from auth.auth_code_url_generator import AuthCodeUrlGenerator
from auth.get_access_token import getAccessToken

load_dotenv()

api_key = os.getenv("api_key")
secret_key = os.getenv("secret_key")
redirect_url = os.getenv("redirect_url")
state = os.getenv("state")


auth_url = AuthCodeUrlGenerator(api_key=api_key, redirect_url=redirect_url, state=state)

print("---------------------------------------")
print(auth_url)
print("---------------------------------------")

auth_redirected_url = input("Please Enter The Redirected Url : ")

auth_code = auth_redirected_url[
    auth_redirected_url.index("code=") + 5 : auth_redirected_url.index("&state")
]

access_token = getAccessToken(
    code=auth_code,
    client_id=api_key,
    client_secret=secret_key,
    redirect_uri=redirect_url,
)
