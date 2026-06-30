import os
import urllib.request
import xml.etree.ElementTree as ET
import json

# 1. DATEN HOLEN (RSS Feed vom OpenAI Blog)
print("Hole aktuelle News...")
url = "https://openai.com/news/rss.xml"
response = urllib.request.urlopen(url)
rss_data = response.read()

# RSS XML parsen, um den neuesten Artikel zu finden
root = ET.fromstring(rss_data)
latest_item = root.find(".//item")
title = latest_item.find("title").text
link = latest_item.find("link").text
description = latest_item.find("description").text

# 2. KI FRAGEN (Mistral API)
print("KI analysiert den Artikel mit Mistral...")
# Wichtig: Die Umgebungsvariable heißt jetzt MISTRAL_API_KEY
api_key = os.environ.get(G2LHxeHhhu3VloA8HMzubnTLF1SRIeET) 

prompt = f"""
Du bist ein präziser Tech-Analyst. Analysiere diesen Artikel:
Titel: {title}
Inhalt: {description}

Gib mir ein valides JSON-Objekt zurück. 
Das JSON MUSS exakt diese Struktur haben:
{{
  "score": (Eine Zahl von 1 bis 10, wie wichtig/weltverändernd die News ist),
  "begruendung": "In einem kurzen Satz, warum der Score so gewählt wurde",
  "zusammenfassung": "Eine knackige Zusammenfassung auf Deutsch (max. 3 Sätze)"
}}
"""

# Mistral API Konfiguration
data = {
    "model": "mistral-small-latest",
    "messages": [{"role": "user", "content": prompt}],
    "response_format": {"type": "json_object"} # Zwingt Mistral zu JSON!
}

req = urllib.request.Request(
    "https://api.mistral.ai/v1/chat/completions",
    data=json.dumps(data).encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
)

# API-Anfrage ausführen
try:
    with urllib.request.urlopen(req) as api_response:
        res_data = json.loads(api_response.read().decode("utf-8"))
        # Bei Mistral steckt die Antwort in choices -> message -> content
        ai_json_string = res_data["choices"][0]["message"]["content"]
        ki_ergebnis = json.loads(ai_json_string)
except Exception as e:
    print(f"Fehler bei der Mistral API: {e}")
    # Fallback-Werte, falls etwas schiefgeht
    ki_ergebnis = {
        "score": 0, 
        "begruendung": "Fehler bei der Analyse", 
        "zusammenfassung": "API Limit erreicht oder Netzwerkfehler."
    }

# 3. HTML-WEBSITE GENERIEREN
print("Generiere Website...")
html_content = f"""
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autonome KI-News</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; color: #333; padding: 40px; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
        h1 {{ color: #007bb5; border-bottom: 2px solid #f4f7f6; padding-bottom: 10px; }}
        .badge {{ background: #ff7043; color: white; padding: 5px 12px; border-radius: 20px; font-size: 0.9em; font-weight: bold; }}
        .score {{ font-size: 1.5em; font-weight: bold; color: #e67e22; margin: 15px 0; }}
        .link-btn {{ display: inline-block; background: #007bb5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
        .meta {{ color: #7f8c8d; font-size: 0.9em; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <span class="badge">Powered by Mistral AI</span>
        <h1>Top KI-News des Tages</h1>
        <h2>{title}</h2>
        <div class="score">KI-Impact-Score: {ki_ergebnis['score']}/10</div>
        <p><strong>Warum?</strong> {ki_ergebnis['begruendung']}</p>
        <hr>
        <h3>KI-Zusammenfassung (Deutsch):</h3>
        <p>{ki_ergebnis['zusammenfassung']}</p>
        <a href="{link}" target="_blank" class="link-btn">Originalen Artikel lesen</a>
    </div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("Fertig! Website wurde erstellt.")