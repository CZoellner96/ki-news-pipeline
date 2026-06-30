import os
import urllib.request
import xml.etree.ElementTree as ET
import json
import time  # NEU: Wird für die Pause zwischen den API-Anfragen benötigt

# 1. UNSERE QUELLEN (Renommierte Tech-Magazine und Forschungslabore)
rss_feeds = [
    {"name": "OpenAI Official", "url": "https://openai.com/news/rss.xml"},
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"name": "Google DeepMind", "url": "https://deepmind.google/blog/rss.xml"},
    {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/"}
]

api_key = os.environ.get("MISTRAL_API_KEY")

# 2. HTML-GRÜST VORBEREITEN
# Wir öffnen das HTML-Dokument schon hier, bevor die Schleife beginnt
html_content = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autonome KI-News</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; background-color: #fafbfc; color: #24292e; padding: 40px; margin: 0; }
        .container { max-width: 750px; margin: 40px auto; background: white; padding: 40px; border: 1px solid #e1e4e8; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        h1 { color: #ff7043; font-size: 24px; border-bottom: 1px solid #e1e4e8; padding-bottom: 15px; margin-top: 0; }
        h2 { font-size: 20px; color: #0366d6; margin-top: 5px; }
        .badge { background: #ff7043; color: white; padding: 4px 10px; border-radius: 3px; font-size: 12px; font-weight: bold; }
        .source-badge { background: #6c757d; color: white; padding: 4px 10px; border-radius: 12px; font-size: 11px; margin-bottom: 10px; display: inline-block; font-weight: bold; }
        .score { font-size: 18px; font-weight: bold; color: #28a745; margin: 20px 0; background: #f1f8ff; padding: 10px; border-left: 4px solid #0366d6; }
        .link-btn { display: inline-block; background: #0366d6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; margin-top: 20px; }
        .link-btn:hover { background: #0056b3; }
        hr { border: 0; border-top: 1px solid #e1e4e8; margin: 35px 0; }
        p { line-height: 1.6; }
    </style>
</head>
<body>
    <div class="container">
        <span class="badge">Pipeline v2.0 (Multi-Source Aggregator)</span>
        <h1>Das KI-Briefing des Tages</h1>
        <hr>
"""

# 3. DIE SCHLEIFE (Geht jeden Feed in unserer Liste nacheinander durch)
for feed in rss_feeds:
    print(f"Lese Feed: {feed['name']}...")
    
    try:
        # Tarnkappen-Modus für den Serverabruf
        req = urllib.request.Request(feed['url'], headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        rss_data = response.read()
        
        # XML parsen und nur den obersten Artikel nehmen
        root = ET.fromstring(rss_data)
        latest_item = root.find(".//item")
        
        # Sicherheits-Check: Falls ein Feed mal unvollständig ist
        title = latest_item.find("title").text if latest_item.find("title") is not None else "Kein Titel"
        link = latest_item.find("link").text if latest_item.find("link") is not None else "#"
        description = latest_item.find("description").text if latest_item.find("description") is not None else "Keine Beschreibung"
        
        # Text kürzen, falls RSS-Feeds zu viele HTML-Bilder im Text verstecken (spart API-Kosten)
        if description and len(description) > 1000:
            description = description[:1000] + "..."
            
        print(f"Artikel gefunden: {title}")
        
        # Mistral KI Prompt
        prompt = f"""
        Du bist ein präziser Tech-Analyst. Analysiere diesen Artikel:
        Titel: {title}
        Inhalt: {description}

        Gib mir ein valides JSON-Objekt zurück. Struktur:
        {{
          "score": (Zahl 1-10 für Wichtigkeit),
          "begruendung": "Kurzer Satz zur Score-Begründung",
          "zusammenfassung": "Zusammenfassung auf Deutsch (max. 3 Sätze)"
        }}
        """
        
        api_daten = {
            "model": "mistral-small-latest",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }
        
        anfrage = urllib.request.Request(
            "https://api.mistral.ai/v1/chat/completions",
            data=json.dumps(api_daten).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        )
        
        # API aufrufen
        with urllib.request.urlopen(anfrage) as api_response:
            res_data = json.loads(api_response.read().decode("utf-8"))
            ki_ergebnis = json.loads(res_data["choices"][0]["message"]["content"])
            
        # 4. DATEN ANS HTML ANHÄNGEN
        # Mit += fügen wir den neuen Artikel einfach unten an die bisherige Website dran
        html_content += f"""
        <div class="source-badge">Quelle: {feed['name']}</div>
        <h2>{title}</h2>
        <div class="score">KI-Impact-Score: {ki_ergebnis.get('score', 0)}/10</div>
        <p><strong>Analysten-Meinung:</strong> {ki_ergebnis.get('begruendung', '')}</p>
        <h3>Automatische Zusammenfassung:</h3>
        <p>{ki_ergebnis.get('zusammenfassung', '')}</p>
        <a href="{link}" target="_blank" class="link-btn">Originalen Artikel lesen &rarr;</a>
        <hr>
        """
        
        print("Erfolgreich! Pausiere 3 Sekunden für Rate-Limit...")
        time.sleep(3) # Die wichtige Pause zwischen den Quellen
        
    except Exception as e:
        print(f"Fehler bei {feed['name']}: {e}")
        # Falls eine Website down ist, stürzt nicht alles ab, sondern wir schreiben eine kleine Fehlermeldung ins HTML
        html_content += f"<p><em>Fehler beim Laden der News von {feed['name']}.</em></p><hr>"

# 5. HTML ABSCHLIESSEN UND SPEICHERN
html_content += """
    </div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("Komplettes Dashboard wurde erstellt!")
