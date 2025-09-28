def AuthCodeUrlGenerator(api_key, redirect_url, state):
    return f"https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={api_key}&redirect_uri={redirect_url}&state=\{state}"
