1. Projektname & Ziel
Projekt: anker-x1-dev-dashboard
Ziel: Ein leichtgewichtiges, selbst gehostetes Web-Dashboard (keine Mobile App), das nur über die Python-Library die Anker-Cloud abfragt und alle relevanten X1-Werte live anzeigt.
Entwickler-freundlich: REST + WebSocket, einfache Erweiterung, Logging, Rate-Limit-Schutz, Export-Funktionen.
2. Unterstützte Hardware & Daten (X1-spezifisch)

Modelle: A5101 (X1 P6K), A5102/A5103 (Energy Module), A5220 (Battery)
Verfügbare Werte (aus api.sites + update_device_energy):
average_power: charge_power_avg, solar_power_avg, home_usage_avg, grid_import_avg, grid_export_avg
state_of_charge (SOC in %)
Energiefluss (PV → Batterie → Haus → Netz)
Tages-Energie: Ertrag, Verbrauch, Einspeisung, Batterie-Lade-/Entlade-Energie
Site-Status, System-Modus, Fehlermeldungen


Wichtig: Kein MQTT-Realtime für X1 → nur Cloud-Polling (max. alle 60 Sekunden sinnvoll). update_device_energy ist auf 10–12 Aufrufe/Minute limitiert.
3. Technischer Stack (empfohlen – minimal & modern)
Backend:

FastAPI (Python 3.12/3.13)
thomluther/anker-solix-api (via poetry)
aiohttp + asyncio (für parallele Updates)
uvicorn + websockets
Redis (optional, für Cache + Rate-Limit)

Frontend:

React 18 + Vite + TailwindCSS + Recharts (für schöne Energiefluss-Grafiken)
Oder Alternative für schnelle DEV-Version: Streamlit (in 2 Stunden fertig)

Deployment:

Docker + docker-compose (eine Container für API + Redis)
Optional: Nginx als Reverse-Proxy

4. Architektur
textClient (Browser) 
  ↓ WebSocket / REST
FastAPI Backend
  ↓ alle 60s
AnkerSolixApi (thomluther)
  ↓ Cloud (ankerpower-api-eu.anker.com)

Singleton AnkerSolixClient-Klasse mit Hintergrund-Task (BackgroundTasks)
Cache in Redis (TTL 55s) → verhindert Rate-Limit-Fehler
Automatischer Re-Login bei Token-Ablauf

5. API-Endpunkte (REST + WebSocket)















































MethodeEndpointBeschreibungReturnGET/statusAktueller System-Status + letzte Update-ZeitJSONGET/powerLive-Leistung + SOC + EnergieflussJSONGET/energy/todayTageswerte (Ertrag, Verbrauch etc.)JSONGET/history?days=7Historische Daten (CSV-Export möglich)JSONWS/ws/livePush alle 60s (oder on-demand)JSON-StreamPOST/trigger-updateManuelles Update triggern200
Beispiel-Response /power:
JSON{
  "timestamp": "2026-03-22T12:51:00Z",
  "soc": 68,
  "solar_kw": 4.2,
  "battery_kw": -1.8,          // negativ = Entladung
  "home_kw": 5.9,
  "grid_kw": 3.5,
  "flow": "PV → Battery → Home + Grid"
}
6. Dashboard-Features (UI)

Live-Übersicht (große Kacheln): SOC (mit Fortschrittsring), PV-Erzeugung, Verbrauch, Netz, Batterie-Status
Energiefluss-Diagramm (Sankey oder animierter Flow wie in der App)
24h-Grafik (Recharts Line-Chart)
Tages-/Wochen-/Monats-Statistiken
Export-Buttons: JSON / CSV / PNG
Alerts (Browser-Notification bei SOC < 20 % oder Fehler)
Dark-Mode + Responsive (auch auf Tablet gut nutzbar)

7. Security & Best Practices

Credentials nur via .env (niemals im Code!)
Rate-Limit-Schutz (max 1x pro 55s)
Logging (structlog) + Error-Reporting
Optional: Basic-Auth oder API-Key für den Dashboard-Zugriff
Wichtig: Account darf nicht gleichzeitig in der Anker-App aktiv sein (Token-Konflikt) → zweiter Account empfohlen

8. Schnellstart-Code-Snippet (Backend-Core)
Python# anker_client.py
from anker_solix_api.api import AnkerSolixApi
import asyncio

class AnkerX1Client:
    def __init__(self):
        self.api = None
        self.last_update = None
        self.data = {}

    async def start(self):
        async with ClientSession() as session:
            self.api = AnkerSolixApi(user, pw, country, session, logger)
            while True:
                await self.api.update_sites()
                await self.api.update_device_energy()
                self.data = self._extract_x1_data()
                self.last_update = datetime.now()
                await asyncio.sleep(60)
Der Rest (FastAPI + WS + Frontend) ist in < 300 Zeilen fertig.
9. Nächste Schritte für dich / den Dev

Repo klonen: git clone https://github.com/thomluther/anker-solix-api
poetry install
.env mit ANKERUSER, ANKERPASSWORD, ANKERCOUNTRY=DE anlegen
Ich kann dir sofort das komplette FastAPI + React-Template als ZIP-Beschreibung oder GitHub-Gist schicken (sag einfach „Template jetzt“).

Willst du:

die Streamlit-Version (super schnell für DEV, 1 Datei)?
oder die Full-Stack FastAPI + React-Version?
oder direkt den kompletten docker-compose.yml + Code?