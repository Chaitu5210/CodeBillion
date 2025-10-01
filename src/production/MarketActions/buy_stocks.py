import upstox_client
from upstox_client.rest import ApiException


def buy_stocks(Access_Token, instrument_token, quantity):
    configuration = upstox_client.Configuration()
    configuration.access_token = Access_Token
    api_instance = upstox_client.OrderApiV3(upstox_client.ApiClient(configuration))
    body = upstox_client.PlaceOrderV3Request(
        quantity=quantity,
        product="D",
        validity="DAY",
        price=0,
        tag="string",
        instrument_token=instrument_token,
        order_type="MARKET",
        transaction_type="BUY",
        disclosed_quantity=0,
        trigger_price=0.0,
        is_amo=False,
        slice=True,
    )

    try:
        api_response = api_instance.place_order(body)
        print("--- Market Order Placed Successfully ---")
    except ApiException as e:
        print("--- Exception Occurred While Placing Market Order ---")
        print("Exception when calling OrderApiV3->place_order: %s\n" % e)
