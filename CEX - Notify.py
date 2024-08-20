import requests
import time

def fetch_balances(address):
    url = f"https://lcd-osmosis.keplr.app/cosmos/bank/v1beta1/spendable_balances/{address}"
    response = requests.get(url)
    data = response.json()
    balances = data.get('balances', [])

    usdc_decimals = 6

    usdc_balance_raw = next((item['amount'] for item in balances if item['denom'] == 'ibc/D189335C6E4A68B513C10AB227BF1C1D38C746766278BA3EEB4FB14124F1D858'), None)
    usdc_balance = int(usdc_balance_raw) / (10 ** usdc_decimals) if usdc_balance_raw else None

    return usdc_balance

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

def generate_message(label, current_balance, difference):
    return (
        f"\n{label}\n"
        f"USDC balance: {current_balance:.2f}\n"
        f"Change: {difference:+.2f}"
    )

def compare_balances(addresses, token, interval=1):
    previous_balances = {label: fetch_balances(address) for label, address in addresses}

    while True:
        for label, address in addresses:
            time.sleep(interval)
            current_balance = fetch_balances(address)

            previous_balance = previous_balances[label]
            if current_balance is not None and previous_balance is not None:
                if current_balance != previous_balance:
                    difference = current_balance - previous_balance
                    message = generate_message(label, current_balance, difference)
                    print(message)
                    send_line_notification(token, message)

            previous_balances[label] = current_balance

# List of Osmosis addresses with labels
osmosis_addresses = [
    ("CEX 1", "osmo1k6ue45fjgg8yh63d2hakt5a5hyn8yyvvksth4k"),
    ("CEX 2", "osmo152fwqsla5lxfu3sgy65naf7w2up0za8fd54ght"),  # Replace with actual addresses
    ("ALL IN", "osmo1w559qsqcw55fhy8rwe8a9sctac90zzq3z7urpg"),
    # Add more addresses with labels as needed
]

# Your LINE Notify token
line_notify_token = "xBS0AAZouYHV2hJyQEDszjKxb3eoZwf9E4D6vZsRDWO"

compare_balances(osmosis_addresses, line_notify_token)
