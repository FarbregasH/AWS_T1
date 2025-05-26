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

# ─── FETCH FUNCTIONS ────────────────────────────────────────────────────────────
def fetch_balances(address, retries=3, delay=5):
    url = f"https://lcd-neutron.keplr.app/cosmos/bank/v1beta1/spendable_balances/{address}"
    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            balances = resp.json().get('balances', [])
            usdc_raw  = next((b['amount'] for b in balances if b['denom']=='ibc/B559A80D62249C8AA07A380E2A2BEA6E5CA9A6F079C912C3A9E9B494105E4F81'), None)
            astro_raw = next((b['amount'] for b in balances if b['denom'].startswith('factory/') and '/astro' in b['denom']), None)
            usdc  = int(usdc_raw)  / 10**6 if usdc_raw  else 0
            astro = int(astro_raw) / 10**6 if astro_raw else 0
            return usdc, astro
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Neutron balances for {address}: {e}")
            if attempt < retries-1:
                time.sleep(delay)
            else:
                return 0, 0

def fetch_uluna_balance(address, retries=3, delay=5):
    url = f"https://phoenix-lcd.terra.dev/cosmos/bank/v1beta1/balances/{address}"
    for attempt in range(1, retries+1):
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 429:
                ra = int(resp.headers.get('Retry-After', delay))
                print(f"Rate limited on Terra {address}: sleeping {ra}s")
                time.sleep(ra)
                continue
            resp.raise_for_status()
            balances = resp.json().get('balances', [])
            raw = next((b['amount'] for b in balances if b['denom']=='uluna'), None)
            return int(raw) / 10**6 if raw else 0
        except requests.exceptions.RequestException as e:
            print(f"Error fetching LUNA for {address} (attempt {attempt}): {e}")
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
def compare_balances(neutron_addresses, terra_addresses, interval=3):
    # snapshots
    prev_neutron = {lbl: fetch_balances(addr) for lbl, addr in neutron_addresses}
    prev_luna    = {lbl: fetch_uluna_balance(addr) for lbl, addr in terra_addresses}

    while True:
        time.sleep(interval)

        # Terra addresses
        for tlabel, taddr in terra_addresses:
            curr = fetch_uluna_balance(taddr)
            prev = prev_luna[tlabel]
            print(f"Checking LUNA for {tlabel} ({taddr})...")
            print(f"Previous LUNA: {prev}")
            print(f"Current LUNA:  {curr}")
            if curr != prev and abs(curr-prev) > 3:
                msg = generate_message(f"Terra ({tlabel})", "LUNA", curr, curr-prev)
                print(msg)
                send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, msg)
            prev_luna[tlabel] = curr

        # Neutron addresses
        for nlabel, naddr in neutron_addresses:
            curr_usdc, curr_astro = fetch_balances(naddr)
            prev_usdc, prev_astro = prev_neutron[nlabel]
            print(f"Checking USDC for {nlabel} ({naddr})...")
            print(f"Previous USDC: {prev_usdc}")
            print(f"Current USDC:  {curr_usdc}")
            if curr_usdc != prev_usdc:
                msg = generate_message(nlabel, "USDC", curr_usdc, curr_usdc-prev_usdc)
                print(msg)
                send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, msg)

            print(f"Checking ASTRO for {nlabel} ({naddr})...")
            print(f"Previous ASTRO: {prev_astro}")
            print(f"Current ASTRO:  {curr_astro}")
            if curr_astro != prev_astro:
                msg = generate_message(nlabel, "ASTRO", curr_astro, curr_astro-prev_astro)
                print(msg)
                send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, msg)

            prev_neutron[nlabel] = (curr_usdc, curr_astro)

# ─── USAGE ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    neutron_addresses = [
        ("BOT_ASTRO_LUNA", "neutron1vzvagczrx7xz28g8wvqwettdaeyhgyn6a99774"),
        ("MM_ASTRO",       "neutron16a6fuc6ruzmt0vu8gwjwrah3zdgr9wtl0h7lfy"),
        ("CX_ASTRO",       "neutron1k6ue45fjgg8yh63d2hakt5a5hyn8yyvv6539er"),
        ("CEX1_ASTRO",     "neutron152fwqsla5lxfu3sgy65naf7w2up0za8fps06m7"),
        ("CEX2_ASTRO",     "neutron1k6ue45fjgg8yh63d2hakt5a5hyn8yyvv6539er")
    ]
    terra_addresses = [
        ("MM_LUNA",   "terra1y60403dd3wvvpswc8l4hy523lftuyzswlru2xf"),
        ("CEX1_LUNA", "terra1gufhwy2cqwz6dzv4u08j2tyh0qvdz9fr0cf2ca"),
        ("CEX2_LUNA", "terra1fna9thvd0sgf0exll0ku8jj6eqalyxld5wq86h")
    ]
    compare_balances(neutron_addresses, terra_addresses, interval=3)
