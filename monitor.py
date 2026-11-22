

import os

import json

import urllib.request

import urllib.parse

from datetime import datetime, timezone

BASE = "https://api.bitvavo.com/v2"

STATE_FILE = "portefeuille.json"
TRANSACTIEBESTAND = "transacties.json"
START_BUDGET = 5000.0

BUY_EUR = 200.0

MAX_POSITIONS = 3

MIN_VOLUME = 250000.0
MAX_SPREAD = 1.0

MIN_RISE = 2.0

MAX_RISE = 6.0

TAKE_PROFIT = 0.05

STOP_LOSS = 0.03

FEE_RATE = 0.0025

def ophalen(endpoint):

    req = urllib.request.Request(

        BASE + endpoint,

        headers={"User-Agent": "BitvavoMonitor/2.0"}

    )

    with urllib.request.urlopen(req, timeout=25) as r:

        return json.load(r)

def getal(value):

    try:

        return float(value)

    except (TypeError, ValueError):

        return 0.0

def telegram(bericht):

    token = os.environ.get("TELEGRAM_BOT_TOKEN")

    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:

        print("Telegram-instellingen ontbreken")

        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    data = urllib.parse.urlencode({

        "chat_id": chat_id,

        "text": bericht

    }).encode("utf-8")

    req = urllib.request.Request(url, data=data, method="POST")

    with urllib.request.urlopen(req, timeout=20) as r:

        print("Telegram-status:", r.status)

def laad_status():

    try:

        with open(STATE_FILE, "r", encoding="utf-8") as f:

            data = json.load(f)

    except (FileNotFoundError, ValueError):

        data = {}

    if not isinstance(data, dict):

        data = {}

    return {

        "cash": getal(data.get("cash", START_BUDGET)),

        "positions": data.get("positions", {}),

        "alerts": data.get("alerts", {})

    }

def bewaar_status(status):

    with open(STATE_FILE, "w", encoding="utf-8") as f:

        json.dump(status, f, indent=2)
def bewaar_transactie(transactie):

    try:

        with open(TRANSACTIEBESTAND, "r", encoding="utf-8") as f:

            transacties = json.load(f)

    except (FileNotFoundError, ValueError):

        transacties = []

    if not isinstance(transacties, list):

        transacties = []

    transacties.append(transactie)

    with open(TRANSACTIEBESTAND, "w", encoding="utf-8") as f:

        json.dump(transacties, f, indent=2)
def maak_dagrapport(status, koersen):

    cash = getal(status["cash"])

    posities = status["positions"]

    waarde_posities = 0.0

    for naam, positie in posities.items():

        koers = koersen.get(naam)

        if koers is None:

            return None

        aantal = getal(positie["amount"])

        waarde_posities += aantal * koers * (1 - FEE_RATE)

    totaal = cash + waarde_posities

    resultaat = totaal - START_BUDGET

    return (

        "BITVAVO FICTIEF DAGrapport\n\n"

        f"Startkapitaal: EUR {START_BUDGET:.2f}\n"

        f"Vrij geld: EUR {cash:.2f}\n"

        f"Waarde open posities: EUR {waarde_posities:.2f}\n"

        f"Totale portefeuille: EUR {totaal:.2f}\n"

        f"Totaal resultaat: EUR {resultaat:+.2f}\n"

        f"Open posities: {len(posities)}\n\n"

        "Alle bedragen zijn fictief."
    )
def main():

    status = laad_status()

    positions = status["positions"]

    alerts = status["alerts"]

    markten = ophalen("/markets")

    tickers = ophalen("/ticker/24h")
    orderboeken = ophalen("/ticker/book")

    eur_markten = {

        m["market"] for m in markten

        if m.get("quote") == "EUR"

        and m.get("status") == "trading"

    }
   

    spreads = {}

    for boek in orderboeken:

        naam = boek.get("market", "")

        bied = getal(boek.get("bid"))

        laat = getal(boek.get("ask"))

        if bied > 0 and laat > 0 and laat >= bied:

            spreads[naam] = (laat - bied) / laat * 100
    kandidaten = []

    koersen = {}

    for t in tickers:

        naam = t.get("market", "")

        if naam not in eur_markten:

            continue

        koers = getal(t.get("last"))

        opening = getal(t.get("open"))

        volume = getal(t.get("volumeQuote"))

        if koers <= 0 or opening <= 0:

            continue

        koersen[naam] = koers

        stijging = (koers / opening - 1) * 100


        if naam not in spreads or spreads[naam] > MAX_SPREAD:
            continue
            
        if (

            MIN_RISE <= stijging <= MAX_RISE

            and volume >= MIN_VOLUME

        ):

            kandidaten.append((volume, naam, koers, stijging))

    kandidaten.sort(reverse=True)

    berichten = []

    # Controleer eerst bestaande fictieve posities.

    for naam, positie in list(positions.items()):

        if naam not in koersen:

            continue

        koers = koersen[naam]

        aankoop = getal(positie["buy_price"])

        aantal = getal(positie["amount"])

        if aankoop <= 0 or aantal <= 0:

            continue

        rendement = (

            koers * (1 - FEE_RATE) /

            (aankoop * (1 + FEE_RATE)) - 1

        )

        if rendement >= TAKE_PROFIT or rendement <= -STOP_LOSS:

            waarde = aantal * koers * (1 - FEE_RATE)

            status["cash"] += waarde

            winst = waarde - (

                aantal * aankoop * (1 + FEE_RATE)

            )

            reden = (

                "Winstdoel bereikt"

                if rendement >= TAKE_PROFIT

                else "Verliesgrens bereikt"

            )
            bewaar_transactie({

                "datum": datetime.now(timezone.utc).isoformat(),

                "type": "VERKOOP",

                "munt": naam,

                "aantal": aantal,

                "aankoopkoers": aankoop,

                "verkoopkoers": koers,

                "opbrengst_eur": round(waarde, 2),

                "kosten_eur": round(aantal * koers * FEE_RATE, 2),

                "resultaat_eur": round(winst, 2),

                "reden": reden

            })
            berichten.append(

                "MOGELIJK VERKOPEN\n"

                f"Munt: {naam}\n"

                f"Huidige koers: EUR {koers:.8g}\n"

                f"Reden: {reden}\n"

                f"Fictief resultaat: EUR {winst:+.2f}\n"

                "De proefpositie wordt fictief gesloten."

            )

            del positions[naam]

            alerts.pop(naam, None)

    # Zoek nieuwe mogelijke koopkansen.

    for _, naam, koers, stijging in kandidaten:

        if len(positions) >= MAX_POSITIONS:

            break

        if naam in positions or naam in alerts:

            continue

        if status["cash"] < BUY_EUR:

            break

        aantal = BUY_EUR / (koers * (1 + FEE_RATE))

        status["cash"] -= BUY_EUR

        positions[naam] = {

            "buy_price": koers,

            "amount": aantal

        }

        alerts[naam] = True
        bewaar_transactie({

            "datum": datetime.now(timezone.utc).isoformat(),

            "type": "AANKOOP",

            "munt": naam,

            "aantal": aantal,

            "aankoopkoers": koers,

            "bedrag_eur": BUY_EUR,

            "kosten_eur": round(

                BUY_EUR * FEE_RATE / (1 + FEE_RATE), 2

            )

        })
        berichten.append(

            "MOGELIJK KOPEN\n"

            f"Munt: {naam}\n"

            f"Koers: EUR {koers:.8g}\n"

            f"Stijging afgelopen 24 uur: {stijging:+.2f}%\n"

            f"Fictief aankoopbedrag: EUR {BUY_EUR:.2f}\n"

            "Waarom? De munt stijgt en wordt "

            "voldoende verhandeld.\n"

            "Let op: dit is geen garantie op winst."

        )

    bewaar_status(status)

    print("Controle uitgevoerd:",

          datetime.now(timezone.utc).isoformat())

    print("EUR-markten:", len(eur_markten))

    print("Fictieve vrije euro's:", round(status["cash"], 2))

    print("Open fictieve posities:", len(positions))

    for bericht in berichten:

        telegram(bericht)

    if not berichten:

        print("Geen nieuwe koop- of verkoopmeldingen.")

    if os.environ.get("DAGRAPPORT") == "1" and datetime.now().hour == 20:

        rapport = maak_dagrapport(status, koersen)

        if rapport is not None:

            telegram(rapport)

        else:

            print("Dagrapport overgeslagen: koers ontbreekt.")

if __name__ == "__main__":

    main()
