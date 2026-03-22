import streamlit as st
import asyncio
from aiohttp import ClientSession
from api.api import AnkerSolixApi
import os
from dotenv import load_dotenv
from datetime import datetime
import json
import logging

# Lade Umgebungsvariablen
load_dotenv()

USER = os.getenv("ANKERUSER")
PASSWORD = os.getenv("ANKERPASSWORD")
COUNTRY = os.getenv("ANKERCOUNTRY", "DE")

st.set_page_config(page_title="Anker X1 Dashboard", page_icon="⚡", layout="wide")

async def fetch_anker_data():
    """Holt die Daten asynchron von der Anker Cloud."""
    logger = logging.getLogger(__name__)
    async with ClientSession() as session:
        api = AnkerSolixApi(USER, PASSWORD, COUNTRY, session, logger)
        await api.update_sites()
        await api.update_device_energy()
        await api.update_device_details()
        return {"sites": api.sites, "devices": api.devices}

# Cache die Daten für 55 Sekunden, um das Anker API Rate-Limit (10-12/Minute) nicht zu reizen.
@st.cache_data(ttl=55)
def get_data():
    if not USER or not PASSWORD:
        return None
    try:
        # Erstelle eine neue Event Loop für Streamlit (da es synchron läuft)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        sites = loop.run_until_complete(fetch_anker_data())
        
        # Streamlit Data Caching funktioniert am besten mit einfachen Dicts, Anker API gibt teils eigene Objekte zurück
        # Ein JSON Roundtrip macht die Daten bombensicher serialisierbar für Streams
        safe_sites = json.loads(json.dumps(sites, default=str))
        return safe_sites
    except Exception as e:
        st.error(f"Fehler beim API Call: {e}")
        return None

# --- UI Aufbau ---

st.title("⚡ Anker X1 Dev Dashboard")

# Credentials Check
if not USER or not PASSWORD:
    st.error("⚠️ Bitte `ANKERUSER` und `ANKERPASSWORD` in der `.env` Datei setzen.")
    st.info("Kopiere `.env.example` zu `.env` und fülle deine echten Daten ein.")
    st.stop()

# Lade Animation inkl. Caching Info
with st.spinner("Lade Daten aus der Anker Cloud (Rate-Limit Cache max. 1x / 55s)..."):
    api_data = get_data()

    if not api_data or not api_data.get("sites"):
        st.warning("Keine Daten gefunden. Bitte Zugangsdaten in der `.env` Datei überprüfen.")
        st.stop()

# Info-Leiste
    sites = api_data.get("sites", {})
    devices = api_data.get("devices", {})

    st.success(f"Daten geladen! (Letztes Update: {datetime.now().strftime('%H:%M:%S')}) - Der Cache läuft nach 55 Sekunden ab.")

    if st.button("🔄 Manuelles Update erzwingen (Cache löschen)", use_container_width=True):
        get_data.clear()
        st.rerun()

    st.markdown("---")

    # Iteration über alle gefundenen Sites (meistens nur 1 Anlage)
    for site_id, site in sites.items():
        site_info = site.get("site_info", {})
        site_name = site_info.get("site_name", "Unbekannt")
        
        st.header(f"🏡 Anlage: {site_name}")
        
        # === DATEN EXTRAKTION X1 (HES) ===
        # Finde das Hauptgerät (meistens in hes_info -> main_sn hinterlegt)
        main_sn = site.get("hes_info", {}).get("main_sn")
        device_data = devices.get(main_sn, {}) if main_sn else {}
        
        # Falls kein main_sn, suche nach einem Gerät mit average_power (Fallback)
        if not device_data:
            for d in devices.values():
                if "average_power" in d:
                    device_data = d
                    break
                    
        power = device_data.get("average_power", {})
        
        # X1 spezifische Power-Werte (sind in kW formatiert als Strings laut debug.json)
        def to_watts(kw_str):
            try:
                return round(float(kw_str) * 1000)
            except:
                return 0

        soc = power.get("state_of_charge", "N/A")
        solar_power = to_watts(power.get("solar_power_avg", 0))
        grid_import = to_watts(power.get("grid_import_avg", 0))
        grid_export = to_watts(power.get("grid_export_avg", 0))
        home_power = to_watts(power.get("home_usage_avg", 0))
        
        charge_p = to_watts(power.get("charge_power_avg", 0))
        discharge_p = to_watts(power.get("discharge_power_avg", 0))
        batt_power = charge_p - discharge_p
        
        # Bestimme Energiefluss Netz (Positiv = Einspeisen, Negativ = Bezug)
        grid_flow = grid_export if grid_export > 0 else -grid_import
    
    # 🔴 LIVE DATEN
    st.subheader("🔴 Live-Leistung")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("SOC (Batterie)", f"{soc} %")
    with col2:
        st.metric("PV-Leistung", f"{solar_power} W")
    with col3:
        st.metric("Batterie-Fluss", f"{batt_power} W", help="Negativ = Entladen | Positiv = Laden")
    with col4:
        st.metric("Haus-Verbrauch", f"{home_power} W")
    
    st.metric("Netz-Fluss", f"{grid_flow} W", help="Negativ = Strombezug | Positiv = Einspeisung")
    
    st.divider()
    
    # 📅 TAGES DATEN
    st.subheader("📅 Tages-Energie")
    energy_today = site.get("energy_details", {}).get("today", {})
    
    t_col1, t_col2, t_col3, t_col4 = st.columns(4)
    with t_col1:
        st.metric("PV-Ertrag heute", f"{energy_today.get('solar', 0)} kWh")
    with t_col2:
        st.metric("Haus-Verbrauch", f"{energy_today.get('home', 0)} kWh")
    with t_col3:
        st.metric("Einspeisung", f"{energy_today.get('grid_export', 0)} kWh")
    with t_col4:
        st.metric("Netzbezug", f"{energy_today.get('grid_import', 0)} kWh")

    st.divider()
    
    # 🐛 DEBUG DATEN
    with st.expander("🛠 Raw JSON API Response (für Debugging der spezifischen X1 Keys)"):
        st.json({"site": site, "device": device_data})
