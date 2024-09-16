import requests

# Fetch the spendable balances from the API
url = "https://lcd-neutron.keplr.app/cosmos/bank/v1beta1/spendable_balances/neutron1v6r5xx4eug7qanhedzj8r0zma42arckrx5jn79"
response = requests.get(url)
data = response.json()

# Extract balances from the response data
balances = data.get('balances', [])

# Define the number of decimals for USDC and ASTRO
usdc_decimals = 6
astro_decimals = 6  # Change this to the correct number of decimals if different

# Find USDC balance and format with decimals
usdc_balance_raw = next((item['amount'] for item in balances if item['denom'] == 'ibc/F082B65C88E4B6D5EF1DB243CDA1D331D002759E938A0F5CD3FFDC5D53B3E349'), None)
if usdc_balance_raw is not None:
    usdc_balance = int(usdc_balance_raw) / (10 ** usdc_decimals)
    print(f"USDC balance: {usdc_balance:.{usdc_decimals}f}")
else:
    print("USDC balance not found")

# Find ASTRO balance and format with decimals
astro_balance_raw = next((item['amount'] for item in balances if item['denom'] == 'factory/neutron1ffus553eet978k024lmssw0czsxwr97mggyv85lpcsdkft8v9ufsz3sa07/astro'), None)
if astro_balance_raw is not None:
    astro_balance = int(astro_balance_raw) / (10 ** astro_decimals)
    print(f"ASTRO balance: {astro_balance:.{astro_decimals}f}")
else:
    print("ASTRO balance not found")
