import upstox_client
from upstox_client.rest import ApiException


def getAccessToken(code, client_id, client_secret, redirect_uri):
    api_instance = upstox_client.LoginApi()
    api_version = "2.0"
    grant_type = "authorization_code"

    try:
        # Get token API
        api_response = api_instance.token(
            api_version,
            code=code,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            grant_type=grant_type,
        )
        return api_response.access_token
    except ApiException as e:
        print("Exception when calling LoginApi->token: %s\n" % e)
