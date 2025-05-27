import requests
import time
import pandas as pd

# ─── CONFIG ────────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = "7928558759:AAHFG41t80_bY1eRyqrPkaFwnXSuV9OfxL4"
TELEGRAM_CHAT_ID = 6501597339  # ← replace with your chat_id

# --- SEI CHAIN CONFIG ---
# List of potential Sei LCD APIs from cosmos.directory/sei.
# We'll try them in order until one works.
SEI_LCD_APIS = [
    "https://lcd-sei.tfl.foundation",  # Original one
    "https://rest.sei-apis.com",
    "https://sei-api.lavenderfive.com",
    # This one had timeouts, keep it lower in the list or remove if consistently unreliable
    "https://sei-api.polkachu.com",
    "https://sei-rest.brocha.in",
    "https://api-sei.stingray.plus",
    "https://sei.api.kjnodes.com",
    "https://sei-rest.publicnode.com",
    "https://1rpc.io/sei-lcd"
]

# CORRECTED USDC IBC denom from your logs (it was CA6FBFAF, not CA6FBFFA):
SEI_USDC_DENOM = "ibc/CA6FBFAF399474A06263E10D0CE5AEBBE15189D6D4B2DD9ADE61007E68EB9DB0"
SEI_TOKEN_DENOM = "usei"  # Native Sei token denom
SEI_DECIMALS = 6  # Confirmed for USDC and common for SEI


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


def fetch_balances(address, token_denom, retries=3, delay=5):
    """
    Fetch a token balance from the Sei chain, trying multiple API endpoints.
    """
    for base_api_url in SEI_LCD_APIS:
        url = f"{base_api_url}/cosmos/bank/v1beta1/spendable_balances/{address}"
        print(f"Attempting to fetch balance from: {url}")  # Debug print

        for attempt in range(retries):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                balances = data.get('balances', [])

                # --- DEBUGGING STEP: Print the raw balances ---
                # print(f"\n--- Raw balances for {address} from {base_api_url} ---")
                # print(balances)
                # print("--------------------------------------------------\n")
                # --- END DEBUGGING STEP ---

                decimals = SEI_DECIMALS
                raw_amount = next((b['amount'] for b in balances if b['denom'] == token_denom), None)

                if raw_amount is None:
                    # print(f"DEBUG: {token_denom} not found in balances from {base_api_url} for {address}.") # Keep if you want this debug line
                    break  # Break from inner retry loop, move to next base_api_url

                return int(raw_amount) / (10 ** decimals)

            except requests.exceptions.RequestException as e:
                print(f"Error fetching {token_denom} from {base_api_url} for {address}: {e}")
                if attempt < retries - 1:
                    print(f"Retrying on {base_api_url} in {delay}s...")
                    time.sleep(delay)
                else:
                    print(f"Max retries exceeded for {base_api_url}. Trying next API if available.")
                    break  # Break from inner retry loop, move to next base_api_url

    print(f"All API attempts failed for {token_denom} for {address}. Returning 0.")
    return 0  # Return 0 if all APIs fail


def generate_balance_message(label, balance, diff, token_name):
    """
    Generates a generic balance change message.
    """
    return (
        f"*{label}* \n"
        f"{token_name} balance: `{balance:.2f}`  \n"
        f"{token_name} change: `{diff:+.2f}`"
    )


def compare_balances(addresses, interval=3):
    # Initial snapshot
    prev = {
        label: {
            'usdc': fetch_balances(addr, SEI_USDC_DENOM),
            'sei_token': fetch_balances(addr, SEI_TOKEN_DENOM),
        }
        for label, addr in addresses
    }

    while True:
        for label, addr in addresses:
            time.sleep(interval)

            # ─── USDC ────────────────────────────────────────────────────────────────
            curr_usdc = fetch_balances(addr, SEI_USDC_DENOM)
            prev_usdc = prev[label]['usdc']

            # always print progress
            print(f"Checking USDC balance for {label}…")
            print(f"Previous balance: {prev_usdc}")
            print(f"Current balance:  {curr_usdc}")

            if curr_usdc != prev_usdc:
                diff = curr_usdc - prev_usdc
                msg = generate_balance_message(label, curr_usdc, diff, "USDC")
                print(msg)  # also log the formatted alert
                send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, msg)
                prev[label]['usdc'] = curr_usdc

            # ─── SEI Token ───────────────────────────────────────────────────────────
            curr_sei_token = fetch_balances(addr, SEI_TOKEN_DENOM)
            prev_sei_token = prev[label]['sei_token']

            print(f"Checking SEI balance for {label}…")
            print(f"Previous balance: {prev_sei_token}")
            print(f"Current balance:  {curr_sei_token}")

            # skip tiny SEI flutters
            if abs(curr_sei_token - prev_sei_token) < 10:  # Adjust threshold as needed
                prev[label]['sei_token'] = curr_sei_token
                continue

            if curr_sei_token != prev_sei_token:
                diff = curr_sei_token - prev_sei_token
                msg = generate_balance_message(label, curr_sei_token, diff, "SEI")
                print(msg)
                send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, msg)
                prev[label]['sei_token'] = curr_sei_token


# ─── USAGE ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sei_addresses = [
        ("CEX1_SEI", "sei1k6ue45fjgg8yh63d2hakt5a5hyn8yyvvn8f399"),
        ("CEX2_SEI", "sei152fwqsla5lxfu3sgy65naf7w2up0za8fgrhw8c"),
    ]
    compare_balances(sei_addresses, interval=3)