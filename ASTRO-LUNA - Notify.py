import requests
import time

# Function to fetch balances from the Neutron blockchain
def fetch_balances(address):
    url = f"https://lcd-neutron.keplr.app/cosmos/bank/v1beta1/spendable_balances/{address}"
    response = requests.get(url)
    data = response.json()
    balances = data.get('balances', [])

    usdc_decimals = 6
    astro_decimals = 6  # Change this if necessary

    usdc_balance_raw = next((item['amount'] for item in balances if item['denom'] == 'ibc/B559A80D62249C8AA07A380E2A2BEA6E5CA9A6F079C912C3A9E9B494105E4F81'), None)
    astro_balance_raw = next((item['amount'] for item in balances if item['denom'] == 'factory/neutron1ffus553eet978k024lmssw0czsxwr97mggyv85lpcsdkft8v9ufsz3sa07/astro'), None)

    usdc_balance = int(usdc_balance_raw) / (10 ** usdc_decimals) if usdc_balance_raw else 0
    astro_balance = int(astro_balance_raw) / (10 ** astro_decimals) if astro_balance_raw else 0

    return usdc_balance, astro_balance

# Function to fetch balance from the Terra blockchain
def fetch_uluna_balance(address):
    url = f"https://phoenix-lcd.terra.dev/cosmos/bank/v1beta1/balances/{address}"
    response = requests.get(url)
    data = response.json()
    balances = data.get('balances', [])

    uluna_decimals = 6  # LUNA is usually represented with 6 decimal places

    uluna_balance_raw = next((item['amount'] for item in balances if item['denom'] == 'uluna'), None)
    uluna_balance = int(uluna_balance_raw) / (10 ** uluna_decimals) if uluna_balance_raw else 0

    return uluna_balance

# Function to send LINE notifications
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

# Function to generate the notification message
def generate_message(token_name, current_balance, difference):
    return (
        f"\nBOT ASTRO"
        f"\n{token_name} Balance: {current_balance:.2f}"
        f"\nChange: {difference:+.2f}"
    )

# Function to monitor balances and notify if there are significant changes
def compare_balances(address_neutron, address_terra, token, interval=1):
    # Initial balance fetch
    previous_usdc_balance, previous_astro_balance = fetch_balances(address_neutron)
    previous_uluna_balance = fetch_uluna_balance(address_terra)

    while True:
        time.sleep(interval)

        # Fetch current balances
        current_usdc_balance, current_astro_balance = fetch_balances(address_neutron)
        current_uluna_balance = fetch_uluna_balance(address_terra)

        # Compare and notify for USDC
        if current_usdc_balance != previous_usdc_balance:
            difference_usdc = current_usdc_balance - previous_usdc_balance
            message = generate_message("USDC", current_usdc_balance, difference_usdc)
            print(message)
            send_line_notification(token, message)

        # Compare and notify for ASTRO
        if current_astro_balance != previous_astro_balance:
            difference_astro = current_astro_balance - previous_astro_balance
            message = generate_message("ASTRO", current_astro_balance, difference_astro)
            print(message)
            send_line_notification(token, message)

        # Compare and notify for LUNA (only if the change is greater than 10)
        if current_uluna_balance != previous_uluna_balance:
            difference_uluna = current_uluna_balance - previous_uluna_balance
            if abs(difference_uluna) > 10:  # Check if the change is greater than 10
                message = generate_message("LUNA", current_uluna_balance, difference_uluna)
                print(message)
                send_line_notification(token, message)

        # Update previous balances
        previous_usdc_balance = current_usdc_balance
        previous_astro_balance = current_astro_balance
        previous_uluna_balance = current_uluna_balance

# Replace with your Neutron and Terra addresses and LINE Notify token
neutron_address = "neutron1vzvagczrx7xz28g8wvqwettdaeyhgyn6a99774"
terra_address = "terra1y60403dd3wvvpswc8l4hy523lftuyzswlru2xf"
line_notify_token = "xBS0AAZouYHV2hJyQEDszjKxb3eoZwf9E4D6vZsRDWO"

# Start monitoring balances
compare_balances(neutron_address, terra_address, line_notify_token)
