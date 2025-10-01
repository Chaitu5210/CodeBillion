import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("sandbox_api_key")
secret_key = os.getenv("sandbox_secret_key")
redirect_url = os.getenv("sandbox_redirect_url")
state = os.getenv("sandbox_state")
access_token = os.getenv("sandbox_access_token")


def SandboxOrchestrator():
    print("Inside SandBox Environment")
