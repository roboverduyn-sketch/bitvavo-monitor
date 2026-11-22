

import json
import os
import urllib.request
import urllib.parse

import xml.etree.ElementTree as ET

from datetime import datetime, timezone
VERZONDEN_BESTAND = "verzonden_nieuws.json"

def laad_verzonden_nieuws():

    try:

        with open(VERZONDEN_BESTAND, "r", encoding="utf-8") as bestand:

            gegevens = json.load(bestand)

            return gegevens if isinstance(gegevens, list) else []

    except (FileNotFoundError, ValueError):

        return []

def bewaar_verzonden_nieuws(gegevens):

    with open(VERZONDEN_BESTAND, "w", encoding="utf-8") as bestand:

        json.dump(gegevens[-500:], bestand, indent=2)
NIEUWSBRONNEN = {

    "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/"

}

def haal_nieuws_op(url):

    verzoek = urllib.request.Request(

        url,

        headers={"User-Agent": "CryptoNieuwsMonitor/1.0"}

    )

    with urllib.request.urlopen(verzoek, timeout=20) as antwoord:

        inhoud = antwoord.read()

    return ET.fromstring(inhoud)
def stuur_telegram(bericht):

    token = os.environ.get("TELEGRAM_BOT_TOKEN")

    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:

        print("Telegram-instellingen ontbreken")

        raise RuntimeError("Telegram-instellingen ontbreken")

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    gegevens = urllib.parse.urlencode({

        "chat_id": chat_id,

        "text": bericht

    }).encode("utf-8")

    verzoek = urllib.request.Request(

        url,

        data=gegevens,

        method="POST"

    )

    with urllib.request.urlopen(verzoek, timeout=20) as antwoord:

        print("Telegram-status:", antwoord.status)
BELANGRIJKE_WOORDEN = [

    "bitcoin", "ethereum", "solana",

    "etf", "sec", "regulation",

    "approval", "listing", "bitvavo",

    "hack", "exploit", "partnership"

]

def is_belangrijk(titel):

    titel = titel.lower()

    return any(

        woord in titel

        for woord in BELANGRIJKE_WOORDEN

    )
def controleer_nieuws():

    for bron, url in NIEUWSBRONNEN.items():

        try:

            nieuws = haal_nieuws_op(url)

            berichten = nieuws.findall(".//item")
            verzonden = laad_verzonden_nieuws()
            if not os.path.exists(VERZONDEN_BESTAND):

                bestaande_links = [

                    item.findtext("link", "").strip()

                    for item in berichten

                    if item.findtext("link", "").strip()

                ]

                bewaar_verzonden_nieuws(bestaande_links)

                print("Eerste controle: bestaande berichten overgeslagen")

                continue
            for item in berichten:

                titel = item.findtext("title", "").strip()

                link = item.findtext("link", "").strip()

                if not titel or not link:

                    continue

                if link in verzonden:

                    continue

                if not is_belangrijk(titel):

                    continue

                bericht = (

                    f"🚨 BELANGRIJK CRYPTONIEUWS\n\n"

                    f"{titel}\n\n"

                    f"Bron: {bron}\n"

                    f"{link}"

                )

                stuur_telegram(bericht)

                verzonden.append(link)

                bewaar_verzonden_nieuws(verzonden)
            print(f"{bron}: {len(berichten)} nieuwsberichten gevonden")

        except Exception as fout:

            print(f"{bron}: ophalen mislukt: {fout}")

if __name__ == "__main__":

    controleer_nieuws()
