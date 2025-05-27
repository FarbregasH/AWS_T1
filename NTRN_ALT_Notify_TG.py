import requests
import time
import pandas as pd

# ─── CONFIG ────────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = "7928558759:AAHFG41t80_bY1eRyqrPkaFwnXSuV9OfxL4"
TELEGRAM_CHAT_ID   = 6501597339  # replace with your chat_id
TOKEN_CSV_PATH     = "/home/ec2-user/AWS_T1/Token_Master_NTRN_ALT.csv"
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

# ─── FETCH FUNCTION ────────────────────────────────────────────────────────────
def fetch_balance(address, denom, retries=3, delay=5):
    """
    Fetch a single token balance via the spendable_balances endpoint.
    """
    url = f"https://lcd-neutron.keplr.app/cosmos/bank/v1beta1/spendable_balances/{address}"
    for attempt in range(1, retries+1):
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            balances = resp.json().get('balances', [])
            raw = next((b['amount'] for b in balances if b['denom']==denom), None)
            return int(raw) if raw else 0
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {denom} for {address} (attempt {attempt}): {e}")
            if attempt < retries:
                time.sleep(delay)
            else:
                return 0
    return 0

# ─── MESSAGE GENERATOR ─────────────────────────────────────────────────────────
def generate_message(label, token_name, current, diff):
    return (
        f"*{label}*  \n"
        f"{token_name}: `{current:.2f}`  \n"
        f"Change: `{diff:+.2f}`"
    )

# ─── MAIN LOOP ─────────────────────────────────────────────────────────────────
def compare_balances(neutron_addresses, interval=3):
    # Load token list and decimal mapping
    token_df = pd.read_csv(TOKEN_CSV_PATH)

    # Initial snapshot for each address: USDC + dynamic tokens
    prev = {}
    for label, addr in neutron_addresses:
        usdc_raw = fetch_balance(addr, 'ibc/B559A80D62249C8AA07A380E2A2BEA6E5CA9A6F079C912C3A9E9B494105E4F81')
        prev[label] = {
            'usdc': usdc_raw / 10**6,
            'tokens': {}
        }
        for _, row in token_df.iterrows():
            raw = fetch_balance(addr, row['token_address'])
            prev[label]['tokens'][row['token_name']] = raw / (10 ** int(row['denom']))

    # Polling loop
    while True:
        time.sleep(interval)
        for label, addr in neutron_addresses:
            # Check USDC
            raw_usdc = fetch_balance(addr, 'ibc/B559A80D62249C8AA07A380E2A2BEA6E5CA9A6F079C912C3A9E9B494105E4F81')
            curr_usdc = raw_usdc / 10**6
            prev_usdc = prev[label]['usdc']
            print(f"Checking USDC for {label}: prev={prev_usdc:.2f}, curr={curr_usdc:.2f}")
            if curr_usdc != prev_usdc:
                msg = generate_message(label, 'USDC', curr_usdc, curr_usdc - prev_usdc)
                print(msg)
                send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, msg)
                prev[label]['usdc'] = curr_usdc

            # Check dynamic tokens
            for _, row in token_df.iterrows():
                name = row['token_name']
                raw = fetch_balance(addr, row['token_address'])
                curr = raw / (10 ** int(row['denom']))
                prev_val = prev[label]['tokens'][name]
                print(f"Checking {name} for {label}: prev={prev_val:.2f}, curr={curr:.2f}")
                if curr != prev_val:
                    msg = generate_message(label, name, curr, curr - prev_val)
                    print(msg)
                    send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, msg)
                    prev[label]['tokens'][name] = curr

# ─── USAGE ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    neutron_addresses = [
        ("CEX1_NTRN_ALT", "neutron152fwqsla5lxfu3sgy65naf7w2up0za8fps06m7"),
    ]
    compare_balances(neutron_addresses, interval=3)
