import requests
import time

# ─── CONFIG ────────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = "7928558759:AAHFG41t80_bY1eRyqrPkaFwnXSuV9OfxL4"
TELEGRAM_CHAT_ID   = 6501597339  # replace with your chat_id
# ────────────────────────────────────────────────────────────────────────────────

def send_telegram_message(bot_token, chat_id, message):
    """
    Send a text message via Telegram bot API.
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        resp = requests.post(url, data=payload, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Telegram message: {e}")

# Function to fetch balances from the Neutron blockchain with retries and delay
def fetch_balances(address, retries=3, delay=5):
    url = f"https://lcd-neutron.keplr.app/cosmos/bank/v1beta1/spendable_balances/{address}"
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            balances = data.get('balances', [])

            usdc_decimals  = 6
            astro_decimals = 6

            usdc_raw   = next((b['amount'] for b in balances
                               if b['denom']== 'ibc/B559A80D62249C8AA07A380E2A2BEA6E5CA9A6F079C912C3A9E9B494105E4F81'),
                              None)
            astro_raw  = next((b['amount'] for b in balances
                               if b['denom'].startswith('factory/') and '/astro' in b['denom']),
                              None)

            usdc_balance  = int(usdc_raw)  / 10**usdc_decimals  if usdc_raw  else 0
            astro_balance = int(astro_raw) / 10**astro_decimals if astro_raw else 0

            return usdc_balance, astro_balance

        except requests.exceptions.RequestException as e:
            print(f"Error fetching balance for {address}: {e}")
            if attempt < retries - 1:
                print(f"Retrying in {delay}s...")
                time.sleep(delay)
            else:
                print("Max retries exceeded. Returning 0,0.")
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

            uluna_decimals = 6
            uluna_raw = next((b['amount'] for b in balances if b['denom']=='uluna'), None)
            return int(uluna_raw) / 10**uluna_decimals if uluna_raw else 0

        except requests.exceptions.RequestException as e:
            print(f"Error fetching LUNA for {address}: {e}")
            if attempt < retries - 1:
                print(f"Retrying in {delay}s...")
                time.sleep(delay)
            else:
                print("Max retries exceeded. Returning 0.")
                return 0

# Function to format the notification message
def generate_message(label, token_name, current, diff):
    return (
        f"*{label}*  \n"
        f"{token_name}: `{current:.2f}`  \n"
        f"Change: `{diff:+.2f}`"
    )

# Main loop: compare balances and notify via Telegram
def compare_balances(neutron_addresses, terra_address, interval=1):
    prev_neutron = {lbl: fetch_balances(addr) for lbl, addr in neutron_addresses}
    prev_luna    = fetch_uluna_balance(terra_address)

    while True:
        time.sleep(interval)
        # Terra LUNA
        curr_luna = fetch_uluna_balance(terra_address)
        if curr_luna != prev_luna and abs(curr_luna - prev_luna) > 3:
            msg = generate_message("Terra (LUNA)", "LUNA", curr_luna, curr_luna - prev_luna)
            print(msg)
            send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, msg)
        prev_luna = curr_luna

        # Neutron tokens
        for label, addr in neutron_addresses:
            curr_usdc, curr_astro = fetch_balances(addr)
            prev_usdc, prev_astro = prev_neutron[label]

            if curr_usdc  != prev_usdc:
                msg = generate_message(label, "USDC",  curr_usdc,  curr_usdc  - prev_usdc)
                print(msg)
                send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, msg)

            if curr_astro != prev_astro:
                msg = generate_message(label, "ASTRO", curr_astro, curr_astro - prev_astro)
                print(msg)
                send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, msg)

            prev_neutron[label] = (curr_usdc, curr_astro)

# ─── USAGE ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    neutron_addresses = [
        ("BOT_ASTRO_LUNA", "neutron1vzvagczrx7xz28g8wvqwettdaeyhgyn6a99774"),
        ("MM_ASTRO",       "neutron16a6fuc6ruzmt0vu8gwjwrah3zdgr9wtl0h7lfy"),
        ("CX_ASTRO",       "neutron1k6ue45fjgg8yh63d2hakt5a5hyn8yyvv6539er"),
        ("CEX1_ASTRO",     "neutron152fwqsla5lxfu3sgy65naf7w2up0za8fps06m7"),
        ("CEX2_ASTRO",     "neutron1k6ue45fjgg8yh63d2hakt5a5hyn8yyvv6539er")
    ]
    terra_address = "terra1y60403dd3wvvpswc8l4hy523lftuyzswlru2xf"
    compare_balances(neutron_addresses, terra_address, interval=3)



