import requests
import time
import pandas as pd

# Load the token data from the CSV file
token_data_path = r"C:\Users\farln\Documents\PycharmProjects\AWS_T1\Token_Master - KC.csv"
token_df = pd.read_csv(token_data_path)

def fetch_balances(address, token_address):
    url = f"https://lcd-osmosis.keplr.app/cosmos/bank/v1beta1/spendable_balances/{address}"
    response = requests.get(url)
    data = response.json()
    balances = data.get('balances', [])

    decimals = 6
    balance_raw = next((item['amount'] for item in balances if item['denom'] == token_address), None)
    balance = int(balance_raw) / (10 ** decimals) if balance_raw else 0

    return balance

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

def generate_usdc_message(label, current_balance, difference, token_name="USDC"):
    return (
        f"\n{label}\n"
        f"{token_name} balance: {current_balance:.2f}\n"
        f"{token_name} change: {difference:+.2f}"
    )

def generate_token_message(label, token_name, token_difference, current_token_balance, token_price):
    return (
        f"\n{label}\n"
        f"{token_name.upper()} change: {token_difference:+.2f}\n"
        f"{token_name.upper()} balance: {current_token_balance:.2f}\n"
        f"{token_name.upper()} price: {token_price:.2f} USD"
    )

def compare_balances(addresses, token, interval=1):
    previous_balances = {
        label: {
            'usdc_balance': fetch_balances(address, 'ibc/498A0751C798A0D9A389AA3691123DADA57DAA4FE165D5C75894505B876BA6E4'),
            'usdc_axl_balance': fetch_balances(address, 'ibc/D189335C6E4A68B513C10AB227BF1C1D38C746766278BA3EEB4FB14124F1D858'),
            'token_balances': {row['token_name']: fetch_balances(address, row['token_address']) for _, row in token_df.iterrows()}
        }
        for label, address in addresses
    }

    while True:
        for label, address in addresses:
            time.sleep(interval)

            # Fetch current balances
            current_usdc_balance = fetch_balances(address, 'ibc/498A0751C798A0D9A389AA3691123DADA57DAA4FE165D5C75894505B876BA6E4')
            current_usdc_axl_balance = fetch_balances(address, 'ibc/D189335C6E4A68B513C10AB227BF1C1D38C746766278BA3EEB4FB14124F1D858')

            previous_usdc_balance = previous_balances[label]['usdc_balance']
            previous_usdc_axl_balance = previous_balances[label]['usdc_axl_balance']

            # Handle USDC balance changes
            if current_usdc_balance != previous_usdc_balance:
                usdc_difference = current_usdc_balance - previous_usdc_balance
                usdc_message = generate_usdc_message(label, current_usdc_balance, usdc_difference, token_name="USDC")
                print(usdc_message)
                send_line_notification(token, usdc_message)
                previous_balances[label]['usdc_balance'] = current_usdc_balance

            # Handle USDC.axl balance changes
            if current_usdc_axl_balance != previous_usdc_axl_balance:
                usdc_axl_difference = current_usdc_axl_balance - previous_usdc_axl_balance
                usdc_axl_message = generate_usdc_message(label, current_usdc_axl_balance, usdc_axl_difference, token_name="USDC.axl")
                print(usdc_axl_message)
                send_line_notification(token, usdc_axl_message)
                previous_balances[label]['usdc_axl_balance'] = current_usdc_axl_balance

            # Handle other token balance changes
            for _, row in token_df.iterrows():
                token_name = row['token_name']
                token_address = row['token_address']

                current_token_balance = fetch_balances(address, token_address)
                previous_token_balance = previous_balances[label]['token_balances'][token_name]

                # Log for debugging
                print(f"Checking {token_name.upper()} balance for {label}...")
                print(f"Previous balance: {previous_token_balance}")
                print(f"Current balance: {current_token_balance}")

                # Skip notification if OSMO change is less than 10
                if token_name.upper() == "OSMO" and abs(current_token_balance - previous_token_balance) < 10:
                    previous_balances[label]['token_balances'][token_name] = current_token_balance
                    continue

                if current_token_balance != previous_token_balance:
                    token_difference = current_token_balance - previous_token_balance

                    # Determine which USDC difference to use based on which changed
                    if current_usdc_balance != previous_usdc_balance:
                        token_price = abs(usdc_difference) / abs(token_difference) if token_difference != 0 else 0
                    elif current_usdc_axl_balance != previous_usdc_axl_balance:
                        token_price = abs(usdc_axl_difference) / abs(token_difference) if token_difference != 0 else 0
                    else:
                        token_price = 0

                    token_message = generate_token_message(label, token_name, token_difference, current_token_balance, token_price)
                    print(token_message)
                    send_line_notification(token, token_message)

                # Update previous balances
                previous_balances[label]['token_balances'][token_name] = current_token_balance

# List of Osmosis addresses with labels
osmosis_addresses = [
    ("KUCOIN", "osmo1tfcyscn264huegdm43a6dt3tmwkfejtyj5qt7j"),
]

# Your LINE Notify token
line_notify_token = "xBS0AAZouYHV2hJyQEDszjKxb3eoZwf9E4D6vZsRDWO"

compare_balances(osmosis_addresses, line_notify_token)




