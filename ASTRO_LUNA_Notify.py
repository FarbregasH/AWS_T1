import requests
import time

# Function to fetch balances from the Neutron blockchain with retries and delay
def fetch_balances(address, retries=3, delay=5):
    url = f"https://lcd-neutron.keplr.app/cosmos/bank/v1beta1/spendable_balances/{address}"
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            balances = data.get('balances', [])

            usdc_decimals = 6
            astro_decimals = 6  # Change this if necessary

            usdc_balance_raw = next((item['amount'] for item in balances if item['denom'] == 'ibc/B559A80D62249C8AA07A380E2A2BEA6E5CA9A6F079C912C3A9E9B494105E4F81'), None)
            astro_balance_raw = next((item['amount'] for item in balances if item['denom'] == 'factory/neutron1ffus553eet978k024lmssw0czsxwr97mggyv85lpcsdkft8v9ufsz3sa07/astro'), None)

            usdc_balance = int(usdc_balance_raw) / (10 ** usdc_decimals) if usdc_balance_raw else 0
            astro_balance = int(astro_balance_raw) / (10 ** astro_decimals) if astro_balance_raw else 0

            return usdc_balance, astro_balance
        except requests.exceptions.RequestException as e:
            print(f"Error fetching balance for {address}: {e}")
            if attempt < retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("Max retries exceeded. Returning 0 balance.")
                return 0, 0

# Function to fetch balance from the Terra blockchain with retries and delay
def fetch_uluna_balance(address, retries=3, delay=5):
    url = f"https://phoenix-lcd.terra.dev/cosmos/bank/v1beta1/balances/{address}"
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            balances = data.get('balances', [])

            uluna_decimals = 6  # LUNA is usually represented with 6 decimal places

            uluna_balance_raw = next((item['amount'] for item in balances if item['denom'] == 'uluna'), None)
            uluna_balance = int(uluna_balance_raw) / (10 ** uluna_decimals) if uluna_balance_raw else 0

            return uluna_balance
        except requests.exceptions.RequestException as e:
            print(f"Error fetching balance for {address}: {e}")
            if attempt < retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("Max retries exceeded. Returning 0 balance.")
                return 0

# Function to send LINE notifications
def send_line_notification(token, message):
    url = "https://notify-api.line.me/api/notify"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    data = {
        "message": message
    }
    try:
        response = requests.post(url, headers=headers, data=data, timeout=10)
        response.raise_for_status()
        print("Notification sent successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send notification: {e}")

# Function to generate the notification message
def generate_message(label, token_name, current_balance, difference):
    return (
        f"\n{label}\n"
        f"{token_name} Balance: {current_balance:.2f}\n"
        f"Change: {difference:+.2f}"
    )

# Function to monitor balances and notify if there are significant changes with logging
def compare_balances(neutron_addresses, terra_address, token, interval=1):
    # Initial balance fetch for all Neutron addresses
    previous_balances = {label: fetch_balances(address) for label, address in neutron_addresses}
    previous_uluna_balance = fetch_uluna_balance(terra_address)

    while True:
        time.sleep(interval)
        current_uluna_balance = fetch_uluna_balance(terra_address)

        # Loop through each Neutron address and compare balances
        for label, neutron_address in neutron_addresses:
            current_usdc_balance, current_astro_balance = fetch_balances(neutron_address)
            previous_usdc_balance, previous_astro_balance = previous_balances[label]

            # Log for debugging
            print(f"Checking USDC balance for {label}...")
            print(f"Previous balance: {previous_usdc_balance}")
            print(f"Current balance: {current_usdc_balance}")

            print(f"Checking ASTRO balance for {label}...")
            print(f"Previous balance: {previous_astro_balance}")
            print(f"Current balance: {current_astro_balance}")

            # Compare and notify for USDC
            if current_usdc_balance != previous_usdc_balance:
                difference_usdc = current_usdc_balance - previous_usdc_balance
                message = generate_message(label, "USDC", current_usdc_balance, difference_usdc)
                print(message)
                send_line_notification(token, message)

            # Compare and notify for ASTRO
            if current_astro_balance != previous_astro_balance:
                difference_astro = current_astro_balance - previous_astro_balance
                message = generate_message(label, "ASTRO", current_astro_balance, difference_astro)
                print(message)
                send_line_notification(token, message)

            # Update previous balances for Neutron addresses
            previous_balances[label] = (current_usdc_balance, current_astro_balance)

        # Compare and notify for LUNA (only if the change is greater than 10)
        print(f"Checking LUNA balance for Terra address...")
        print(f"Previous balance: {previous_uluna_balance}")
        print(f"Current balance: {current_uluna_balance}")

        if current_uluna_balance != previous_uluna_balance:
            difference_uluna = current_uluna_balance - previous_uluna_balance
            if abs(difference_uluna) > 10:  # Check if the change is greater than 10
                message = generate_message("Terra", "LUNA", current_uluna_balance, difference_uluna)
                print(message)
                send_line_notification(token, message)

        # Update previous LUNA balance
        previous_uluna_balance = current_uluna_balance

# Replace with your Neutron addresses and LINE Notify token
neutron_addresses = [
    ("BOT_ASTRO_LUNA", "neutron1vzvagczrx7xz28g8wvqwettdaeyhgyn6a99774"),
    ("MM_ASTRO", "neutron16a6fuc6ruzmt0vu8gwjwrah3zdgr9wtl0h7lfy"),
    ("CX_ASTRO", "neutron1k6ue45fjgg8yh63d2hakt5a5hyn8yyvv6539er")
]
terra_address = "terra1y60403dd3wvvpswc8l4hy523lftuyzswlru2xf"
line_notify_token = "xBS0AAZouYHV2hJyQEDszjKxb3eoZwf9E4D6vZsRDWO"

# Start monitoring balances
compare_balances(neutron_addresses, terra_address, line_notify_token)


