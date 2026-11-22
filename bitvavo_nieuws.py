import urllib.request

url = "https://bitvavo.com/nl/upcoming-listings"

verzoek = urllib.request.Request(

    url,

    headers={"User-Agent": "Mozilla/5.0"}

)

try:

    with urllib.request.urlopen(verzoek, timeout=20) as antwoord:

        inhoud = antwoord.read()

        print("Bitvavo HTTP-status:", antwoord.status)

        print("Ontvangen bytes:", len(inhoud))

except Exception as fout:

    print("Bitvavo ophalen mislukt:", fout)
