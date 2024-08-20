import requests
import time


def fetch_balances(address):
    url = f"https://lcd-osmosis.keplr.app/cosmos/bank/v1beta1/spendable_balances/{address}"
    response = requests.get(url)
    data = response.json()
    balances = data.get('balances', [])

    usdcaxl_decimals = 6
    usdc_decimals = 6

    usdcaxl_balance_raw = next((item['amount'] for item in balances if item[
        'denom'] == 'ibc/D189335C6E4A68B513C10AB227BF1C1D38C746766278BA3EEB4FB14124F1D858'), None)
    usdc_balance_raw = next((item['amount'] for item in balances if
                             item['denom'] == 'ibc/498A0751C798A0D9A389AA3691123DADA57DAA4FE165D5C75894505B876BA6E4'),
                            None)

    usdcaxl_balance = int(usdcaxl_balance_raw) / (10 ** usdcaxl_decimals) if usdcaxl_balance_raw else None
    usdc_balance = int(usdc_balance_raw) / (10 ** usdc_decimals) if usdc_balance_raw else None

    return usdcaxl_balance, usdc_balance


def send_line_notification(token, message):
    url = "https://notify-api.line.me/api/notify"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    data = {
        "message": message
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        print("Notification sent successfully.")
    else:
        print(f"Failed to send notification. Status code: {response.status_code}, Response: {response.text}")


def generate_message(label, usdcaxl_balance=None, usdc_balance=None, usdcaxl_difference=None, usdc_difference=None):
    message_parts = [f"\n{label}\n"]

    if usdcaxl_balance is not None and usdcaxl_difference is not None:
        message_parts.append(f"USDCAXL balance: {usdcaxl_balance:.2f}\nChange: {usdcaxl_difference:+.2f}\n")

    if usdc_balance is not None and usdc_difference is not None:
        message_parts.append(f"USDC balance: {usdc_balance:.2f}\nChange: {usdc_difference:+.2f}\n")

    return "".join(message_parts)


def compare_balances(addresses, token, interval=1):
    previous_balances = {label: fetch_balances(address) for label, address in addresses}

    while True:
        for label, address in addresses:
            time.sleep(interval)
            current_usdcaxl_balance, current_usdc_balance = fetch_balances(address)

            previous_usdcaxl_balance, previous_usdc_balance = previous_balances[label]

            usdcaxl_difference = usdc_difference = None
            if current_usdcaxl_balance is not None and previous_usdcaxl_balance is not None and current_usdcaxl_balance != previous_usdcaxl_balance:
                usdcaxl_difference = current_usdcaxl_balance - previous_usdcaxl_balance

            if current_usdc_balance is not None and previous_usdc_balance is not None and current_usdc_balance != previous_usdc_balance:
                usdc_difference = current_usdc_balance - previous_usdc_balance

            if usdcaxl_difference is not None or usdc_difference is not None:
                message = generate_message(label, current_usdcaxl_balance, current_usdc_balance, usdcaxl_difference,
                                           usdc_difference)
                print(message)
                send_line_notification(token, message)

            previous_balances[label] = (current_usdcaxl_balance, current_usdc_balance)


# List of Osmosis addresses with labels
osmosis_addresses = [
    ("BOT1", "osmo1cys322uqws90eys0szfwyhkamlcukwm9qvf5rm"),
    ("BOT2", "osmo1aqpwydywdl4qcjjet7ch4lhxe2te6ldjrye0py"),  # Replace with actual addresses
    ("BOT3", "osmo1n7vr92emc0dhutrleqddlkpsgdwhz9sw87t0v3"),
    ("BOT4", "osmo1ka4sczlphz4a2skqh50zujffcyy274dphtngds"),
    ("BOT7", "osmo1n2270jpgecxxfffkucfnyp0zffeh4h076s2qru"),
    ("ARCH1", "osmo1w8vcuppj8ryjhkqhj4wms5atntu9s7mysxuyh6"),
    ("ARCH2", "osmo10ez7apnf7f2q4jkqs7jaehc2xd9prm8lvu3hzu"),
    # Add more addresses with labels as needed
]

# Your LINE Notify token
line_notify_token = "xBS0AAZouYHV2hJyQEDszjKxb3eoZwf9E4D6vZsRDWO"

compare_balances(osmosis_addresses, line_notify_token)
