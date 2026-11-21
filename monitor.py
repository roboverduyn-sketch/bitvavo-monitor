import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone

BASE = "https://api.bitvavo.com/v2"
MIN_VOLUME_EUR = 100000
MAX_RESULTS = 5

def ophalen(endpoint):
    req = urllib.request.Request(
        BASE + endpoint,
        headers={"User-Agent": "BitvavoMonitor/1.0"}
    )
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.load(response)

def getal(waarde):
    try:
        return float(waarde)
    except (TypeError, ValueError):
        return 0.0

def analyseer():
    markten = ophalen("/markets")
    tickers = ophalen("/ticker/24h")
    eur_markten = {
        m["market"] for m in markten
        if m.get("quote") == "EUR"
        and m.get("status") == "trading"
    }

    resultaten = []
    for t in tickers:
        naam = t.get("market", "")
        if naam not in eur_markten:
            continue

        koers = getal(t.get("last"))
        opening = getal(t.get("open"))
        volume = getal(t.get("volumeQuote"))

        if koers <= 0 or opening <= 0 or volume < MIN_VOLUME_EUR:
            continue

        verandering = (koers / opening - 1) * 100

        if verandering < 1 or verandering > 12:
            continue

        score = verandering
        resultaten.append((score, naam, koers, verandering, volume))

    resultaten.sort(reverse=True)
    return len(eur_markten), resultaten[:MAX_RESULTS]

def telegram(bericht):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("Telegram-instellingen ontbreken")
        return

    url = "https://api.telegram.org/bot" + token + "/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": bericht
    }).encode("utf-8")

    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=20) as response:
        print("Telegram-status:", response.status)

def main():
    tijd = datetime.now(timezone.utc).strftime("%d-%m-%Y %H:%M UTC")
    aantal, kandidaten = analyseer()

    regels = [
        "BITVAVO MARKTCONTROLE",
        "Tijd: " + tijd,
        "Beschikbare EUR-markten: " + str(aantal),
        ""
    ]

    if kandidaten:
        regels.append("Technische kandidaten:")
        for _, naam, koers, verandering, volume in kandidaten:
            regels.append(
                f"{naam}: EUR {koers:.8g} | "
                f"24u {verandering:+.2f}% | "
                f"volume EUR {volume:,.0f}"
            )
    else:
        regels.append("Geen kandidaten binnen de ingestelde filters.")

    regels.extend([
        "",
        "Dit is een marktscreening, geen koopadvies.",
        "Geen automatische transacties."
    ])

    bericht = "\n".join(regels)
    print(bericht)
    telegram(bericht)

if __name__ == "__main__":
    main()
