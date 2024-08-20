import requests
import time

def fetch_balances(address):
    url = f"https://lcd-neutron.keplr.app/cosmos/bank/v1beta1/spendable_balances/{address}"
    response = requests.get(url)
    data = response.json()
    balances = data.get('balances', [])

    astro_decimals = 6  # Change this if necessary

    astro_balance_raw = next((item['amount'] for item in balances if item['denom'] == 'factory/neutron1ffus553eet978k024lmssw0czsxwr97mggyv85lpcsdkft8v9ufsz3sa07/astro'), None)

    astro_balance = int(astro_balance_raw) / (10 ** astro_decimals) if astro_balance_raw else None

    return astro_balance

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
        f"ASTRO balance: {current_balance:.2f}\n"
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


# List of Neutron addresses with labels
neutron_addresses = [
    ("CX Store", "neutron1xd6rk3vfgd9uylccvpsy26wdzk02erfg4jsl6g"),
    ("CX Receive", "neutron1xudd5xs699955lrzf02hu6kr2nlfvxmj3a7suy"),
    # Add more addresses with labels as needed
]

# Your LINE Notify token
line_notify_token = "xBS0AAZouYHV2hJyQEDszjKxb3eoZwf9E4D6vZsRDWO"

compare_balances(neutron_addresses, line_notify_token)
