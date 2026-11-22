

import json

import urllib.request

import xml.etree.ElementTree as ET

from datetime import datetime, timezone

NIEUWSBRONNEN = {

    "Bitvavo": "https://blog.bitvavo.com/feed/"

}

def haal_nieuws_op(url):

    verzoek = urllib.request.Request(

        url,

        headers={"User-Agent": "CryptoNieuwsMonitor/1.0"}

    )

    with urllib.request.urlopen(verzoek, timeout=20) as antwoord:

        inhoud = antwoord.read()

    return ET.fromstring(inhoud)

def controleer_nieuws():

    for bron, url in NIEUWSBRONNEN.items():

        try:

            nieuws = haal_nieuws_op(url)

            berichten = nieuws.findall(".//item")

            print(f"{bron}: {len(berichten)} nieuwsberichten gevonden")

        except Exception as fout:

            print(f"{bron}: ophalen mislukt: {fout}")

if __name__ == "__main__":

    controleer_nieuws()
