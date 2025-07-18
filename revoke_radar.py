#!/usr/bin/env python3
"""
RevokeRadar — сканирование и подготовка транзакций на отзыв ERC-20 approve().
"""

import os
import time
import requests
from web3 import Web3
from eth_utils import to_checksum_address

# --- Настройки через переменные окружения ---
RPC_URL         = os.getenv("ETH_RPC_URL")            # Ethereum RPC
ETHPLORER_KEY   = os.getenv("ETHPLORER_API_KEY")      # Ethplorer API key
WALLET_ADDRESS  = os.getenv("WALLET_ADDRESS")         # ваш адрес
SPENDERS        = os.getenv("SPENDER_LIST", "")       # comma‑sep список адресов‑спендеров
PRIVATE_KEY     = os.getenv("PRIVATE_KEY")            # опционально, для прямой отправки
DRY_RUN         = os.getenv("DRY_RUN", "true").lower() == "true"
POLL_INTERVAL   = int(os.getenv("POLL_INTERVAL", "3600"))  # интервал проверки (сек)

if not all([RPC_URL, ETHPLORER_KEY, WALLET_ADDRESS, SPENDERS]):
    print("❗ Задайте ETH_RPC_URL, ETHPLORER_API_KEY, WALLET_ADDRESS и SPENDER_LIST")
    exit(1)

w3 = Web3(Web3.HTTPProvider(RPC_URL))
if not w3.is_connected():
    print("❗ Не удалось подключиться к RPC")
    exit(1)

WALLET_ADDRESS = to_checksum_address(WALLET_ADDRESS)
SPENDER_LIST   = [to_checksum_address(s) for s in SPENDERS.split(",")]

ERC20_ABI = [
    {
      "constant":True,
      "inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],
      "name":"allowance","outputs":[{"name":"","type":"uint256"}],
      "type":"function"
    },
    {
      "constant":False,
      "inputs":[{"name":"spender","type":"address"},{"name":"value","type":"uint256"}],
      "name":"approve","outputs":[{"name":"","type":"bool"}],
      "type":"function"
    }
]

def fetch_tokens(owner: str):
    url = f"https://api.ethplorer.io/getAddressInfo/{owner}"
    resp = requests.get(url, params={"apiKey": ETHPLORER_KEY})
    resp.raise_for_status()
    return resp.json().get("tokens", [])

def build_revoke_tx(token_addr: str, spender: str, nonce: int):
    token = w3.eth.contract(address=token_addr, abi=ERC20_ABI)
    return token.functions.approve(spender, 0).build_transaction({
        "from": WALLET_ADDRESS,
        "nonce": nonce,
        "gas": 60000,
        "gasPrice": w3.to_wei("20", "gwei")
    })

def main():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] RevokeRadar старт.")
    while True:
        try:
            tokens = fetch_tokens(WALLET_ADDRESS)
            nonce = w3.eth.get_transaction_count(WALLET_ADDRESS)
            for item in tokens:
                info = item["tokenInfo"]
                token_addr = to_checksum_address(info["address"])
                symbol = info.get("symbol", "?")
                for spender in SPENDER_LIST:
                    allowance = w3.eth.contract(address=token_addr, abi=ERC20_ABI)\
                                     .functions.allowance(WALLET_ADDRESS, spender).call()
                    if allowance > 0:
                        human = allowance / 10**int(info.get("decimals", 18))
                        print(f"🔒 {symbol}: разрешено {human} → revoke@{spender}")
                        tx = build_revoke_tx(token_addr, spender, nonce)
                        if DRY_RUN:
                            print("   • DRY RUN: raw_tx =", tx)
                        else:
                            signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
                            txh = w3.eth.send_raw_transaction(signed.rawTransaction)
                            print("   • отправлено:", txh.hex())
                        nonce += 1
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            print("Выход.")
            break
        except Exception as e:
            print("Ошибка:", e)
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
