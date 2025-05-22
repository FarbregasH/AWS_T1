import requests
import time
import pandas as pd

# ─── CONFIG ────────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = "7928558759:AAHFG41t80_bY1eRyqrPkaFwnXSuV9OfxL4"
TELEGRAM_CHAT_ID   = 6501597339  # ← replace with your chat_id
# ────────────────────────────────────────────────────────────────────────────────

def send_telegram_message(bot_token, chat_id, message):
    """
    Send a text message via Telegram bot API.
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id":    chat_id,
        "text":       message,
        "parse_mode": "Markdown"
    }
    try:
        resp = requests.post(url, data=payload, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Telegram message: {e}")

def fetch_balances(address, token_address, retries=3, delay=5):
    url = f"https://lcd-osmosis.keplr.app/cosmos/bank/v1beta1/spendable_balances/{address}"
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            balances = response.json().get('balances', [])

            decimals   = 6
            raw_amount = next((b['amount'] for b in balances if b['denom']==token_address), None)
            return int(raw_amount) / 10**decimals if raw_amount else 0

        except requests.exceptions.RequestException as e:
            print(f"Error fetching {token_address} for {address}: {e}")
            if attempt < retries - 1:
                print(f"Retrying in {delay}s...")
                time.sleep(delay)
            else:
                print("Max retries exceeded. Returning 0.")
                return 0

def generate_usdc_message(label, balance, diff, token_name="USDC"):
    return (
        f"*{label}*  \n"
        f"{token_name} balance: `{balance:.2f}`  \n"
        f"{token_name} change: `{diff:+.2f}`"
    )

def generate_token_message(label, token_name, diff, balance, price):
    return (
        f"*{label}*  \n"
        f"{token_name.upper()} change: `{diff:+.2f}`  \n"
        f"{token_name.upper()} balance: `{balance:.2f}`  \n"
        f"{token_name.upper()} price: `{price:.2f}` USD"
    )

def compare_balances(addresses, interval=3):
    # Load token list
    token_df = pd.read_csv("/home/ec2-user/AWS_T1/Token_Master_CEX1_MX.csv")

    # Initial snapshot
    prev = {
        label: {
            'usdc':     fetch_balances(addr, 'ibc/498A0751C798A0D9A389AA3691123DADA57DAA4FE165D5C75894505B876BA6E4'),
            'usdc_axl': fetch_balances(addr, 'ibc/D189335C6E4A68B513C10AB227BF1C1D38C746766278BA3EEB4FB14124F1D858'),
            'tokens':   {row['token_name']: fetch_balances(addr, row['token_address'])
                         for _, row in token_df.iterrows()}
        }
        for label, addr in addresses
    }

    while True:
        for label, addr in addresses:
            time.sleep(interval)

            # ─── USDC ────────────────────────────────────────────────────────────────
            curr_usdc = fetch_balances(addr, 'ibc/498A0751C798A0D9A389AA3691123DADA57DAA4FE165D5C75894505B876BA6E4')
            prev_usdc = prev[label]['usdc']

            # always print progress
            print(f"Checking USDC balance for {label}…")
            print(f"Previous balance: {prev_usdc}")
            print(f"Current balance:  {curr_usdc}")

            if curr_usdc != prev_usdc:
                diff = curr_usdc - prev_usdc
                msg  = generate_usdc_message(label, curr_usdc, diff, "USDC")
                print(msg)   # also log the formatted alert
                send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, msg)
                prev[label]['usdc'] = curr_usdc

            # ─── USDC.axl ────────────────────────────────────────────────────────────
            curr_usdc_axl = fetch_balances(addr, 'ibc/D189335C6E4A68B513C10AB227BF1C1D38C746766278BA3EEB4FB14124F1D858')
            prev_usdc_axl = prev[label]['usdc_axl']

            print(f"Checking USDC.axl balance for {label}…")
            print(f"Previous balance: {prev_usdc_axl}")
            print(f"Current balance:  {curr_usdc_axl}")

            if curr_usdc_axl != prev_usdc_axl:
                diff = curr_usdc_axl - prev_usdc_axl
                msg  = generate_usdc_message(label, curr_usdc_axl, diff, "USDC.axl")
                print(msg)
                send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, msg)
                prev[label]['usdc_axl'] = curr_usdc_axl

            # ─── Other tokens ────────────────────────────────────────────────────────
            for _, row in token_df.iterrows():
                tn         = row['token_name']
                addr_token = row['token_address']
                curr_bal   = fetch_balances(addr, addr_token)
                prev_bal   = prev[label]['tokens'][tn]

                print(f"Checking {tn.upper()} balance for {label}…")
                print(f"Previous balance: {prev_bal}")
                print(f"Current balance:  {curr_bal}")

                # skip tiny OSMO flutters
                if tn.upper()=="OSMO" and abs(curr_bal - prev_bal) < 10:
                    prev[label]['tokens'][tn] = curr_bal
                    continue

                if curr_bal != prev_bal:
                    diff = curr_bal - prev_bal

                    # price = USDC change / token change
                    if curr_usdc != prev_usdc:
                        price = abs(curr_usdc - prev_usdc) / abs(diff)
                    elif curr_usdc_axl != prev_usdc_axl:
                        price = abs(curr_usdc_axl - prev_usdc_axl) / abs(diff)
                    else:
                        price = 0

                    msg = generate_token_message(label, tn, diff, curr_bal, price)
                    print(msg)
                    send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, msg)

                prev[label]['tokens'][tn] = curr_bal

# ─── USAGE ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    osmosis_addresses = [
        ("CEX1_MX", "osmo1k6ue45fjgg8yh63d2hakt5a5hyn8yyvvksth4k"),
    ]
    compare_balances(osmosis_addresses, interval=3)

