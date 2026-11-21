import json

import urllib.request

from datetime import datetime, timezone

URL = "https://api.bitvavo.com/v2/ticker/price"

def main():

    request = urllib.request.Request(

        URL,

        headers={"User-Agent": "BitvavoPaperMonitor/1.0"}

    )

    with urllib.request.urlopen(request, timeout=20) as response:

        markets = json.load(response)

    eur_markets = [

        item for item in markets

        if item["market"].endswith("-EUR")

    ]

    print("Controle:", datetime.now(timezone.utc).isoformat())

    print("Aantal EUR-markten:", len(eur_markets))

    for symbol in ("BTC-EUR", "ETH-EUR", "SOL-EUR"):

        match = next(

            (m for m in eur_markets if m["market"] == symbol),

            None

        )

        if match:

            print(symbol, match["price"], "EUR")

if __name__ == "__main__":

    main()
import os

import urllib.parse

def stuur_telegram():

    token = os.environ.get("TELEGRAM_BOT_TOKEN")

    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:

        print("Telegram-instellingen ontbreken")

        return

    bericht = "Bitvavo-monitor: controle uitgevoerd."

    gegevens = urllib.parse.urlencode({

        "chat_id": chat_id,

        "text": bericht

    }).encode("utf-8")

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    verzoek = urllib.request.Request(

        url, data=gegevens, method="POST"

    )

    with urllib.request.urlopen(verzoek, timeout=15) as antwoord:

        print("Telegram:", antwoord.status)

stuur_telegram()
