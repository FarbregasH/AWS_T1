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
def fetch_balances(address):
    url = f"https://lcd-osmosis.keplr.app/cosmos/bank/v1beta1/spendable_balances/{address}"
    response = requests.get(url)
    data = response.json()
    balances = data.get('balances', [])

    usdcaxl_decimals = 6
    usdc_decimals    = 6

    usdcaxl_balance_raw = next((item['amount'] for item in balances \
        if item['denom'] == 'ibc/D189335C6E4A68B513C10AB227BF1C1D38C746766278BA3EEB4FB14124F1D858'), None)
    usdc_balance_raw    = next((item['amount'] for item in balances \
        if item['denom'] == 'ibc/498A0751C798A0D9A389AA3691123DADA57DAA4FE165D5C75894505B876BA6E4'), None)

    usdcaxl_balance = int(usdcaxl_balance_raw) / (10 ** usdcaxl_decimals) if usdcaxl_balance_raw else None
    usdc_balance    = int(usdc_balance_raw)    / (10 ** usdc_decimals)    if usdc_balance_raw    else None

    return usdcaxl_balance, usdc_balance

# ─── MESSAGE GENERATOR ─────────────────────────────────────────────────────────
def generate_message(label, usdcaxl_balance=None, usdc_balance=None,
                     usdcaxl_difference=None, usdc_difference=None):
    message_parts = [f"\n{label}\n"]

    if usdcaxl_balance is not None and usdcaxl_difference is not None:
        message_parts.append(
            f"USDCAXL balance: {usdcaxl_balance:.2f}\nChange: {usdcaxl_difference:+.2f}\n"
        )

    if usdc_balance is not None and usdc_difference is not None:
        message_parts.append(
            f"USDC balance: {usdc_balance:.2f}\nChange: {usdc_difference:+.2f}\n"
        )

    return "".join(message_parts)

# ─── MAIN LOOP ─────────────────────────────────────────────────────────────────
def compare_balances(addresses, interval=1):
    previous_balances = {label: fetch_balances(addr) for label, addr in addresses}

    while True:
        for label, address in addresses:
            time.sleep(interval)
            curr_usdcaxl, curr_usdc = fetch_balances(address)
            prev_usdcaxl, prev_usdc = previous_balances[label]

            usdcaxl_diff = None
            usdc_diff    = None
            if curr_usdcaxl is not None and prev_usdcaxl is not None \
               and curr_usdcaxl != prev_usdcaxl:
                usdcaxl_diff = curr_usdcaxl - prev_usdcaxl

            if curr_usdc is not None and prev_usdc is not None \
               and curr_usdc != prev_usdc:
                usdc_diff = curr_usdc - prev_usdc

            # Log every check
            print(f"Checking {label}: USDCAXL prev={prev_usdcaxl}, curr={curr_usdcaxl}")
            print(f"Checking {label}: USDC    prev={prev_usdc},    curr={curr_usdc}")

            # Only notify if change detected
            if usdcaxl_diff is not None or usdc_diff is not None:
                msg = generate_message(label,
                                       usdcaxl_balance=curr_usdcaxl,
                                       usdc_balance=curr_usdc,
                                       usdcaxl_difference=usdcaxl_diff,
                                       usdc_difference=usdc_diff)
                print(msg)
                send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, msg)

            previous_balances[label] = (curr_usdcaxl, curr_usdc)

# ─── USAGE ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    osmosis_addresses = [
        ("BOT1", "osmo1cys322uqws90eys0szfwyhkamlcukwm9qvf5rm"),
        ("BOT2", "osmo1aqpwydywdl4qcjjet7ch4lhxe2te6ldjrye0py"),
        ("BOT3", "osmo1n7vr92emc0dhutrleqddlkpsgdwhz9sw87t0v3"),
        ("BOT4", "osmo1ka4sczlphz4a2skqh50zujffcyy274dphtngds"),
        ("BOT7", "osmo1n2270jpgecxxfffkucfnyp0zffeh4h076s2qru"),
        ("ARCH1", "osmo1w8vcuppj8ryjhkqhj4wms5atntu9s7mysxuyh6"),
        ("ARCH2", "osmo10ez7apnf7f2q4jkqs7jaehc2xd9prm8lvu3hzu"),
    ]
    compare_balances(osmosis_addresses, interval=1)