"""
Real-world test scenarios for TFL MCP Server
Testing as if a Poke user is asking questions
"""

import sys
import os
sys.path.insert(0, 'src')

from dotenv import load_dotenv
from tfl_client import TFLClient
import json

load_dotenv()

# Initialize client - uses TFL_API_KEY from environment
tfl = TFLClient(api_key=os.environ.get("TFL_API_KEY", ""))

def print_result(title, data):
    print(f"\n{'='*60}")
    print(f"📍 {title}")
    print('='*60)
    if isinstance(data, list):
        for item in data[:5]:  # Limit output
            print(json.dumps(item, indent=2))
    else:
        print(json.dumps(data, indent=2))

# ============================================================
# SCENARIO 1: "I need to get from King's Cross to Heathrow"
# ============================================================
print("\n" + "🚇"*30)
print("SCENARIO 1: Journey from King's Cross to Heathrow Airport")
print("🚇"*30)

try:
    journey = tfl.get_journey("King's Cross", "Heathrow Airport")
    print_result("Journey Options", journey)
except Exception as e:
    print(f"❌ Error: {e}")

# ============================================================
# SCENARIO 2: "What's the tube status right now?"
# ============================================================
print("\n" + "🚇"*30)
print("SCENARIO 2: Current Tube Line Status")
print("🚇"*30)

try:
    status = tfl.get_line_status("tube")
    print_result("Tube Status", status)
except Exception as e:
    print(f"❌ Error: {e}")

# ============================================================
# SCENARIO 3: "When's the next train at Oxford Circus?"
# ============================================================
print("\n" + "🚇"*30)
print("SCENARIO 3: Next trains at Oxford Circus")
print("🚇"*30)

try:
    # First search for the station
    stops = tfl.search_stops("Oxford Circus", "tube")
    print_result("Found stations", stops[:2])

    if stops and stops[0].get('id'):
        stop_id = stops[0]['id']
        arrivals = tfl.get_arrivals(stop_id, limit=5)
        print_result(f"Arrivals at {stop_id}", arrivals)
except Exception as e:
    print(f"❌ Error: {e}")

# ============================================================
# SCENARIO 4: "I'm at postcode SW1A 1AA, get me to E14 5AB"
# (Westminster to Canary Wharf area)
# ============================================================
print("\n" + "🚇"*30)
print("SCENARIO 4: Journey between postcodes (SW1A 1AA to E14 5AB)")
print("🚇"*30)

try:
    journey = tfl.get_journey("SW1A 1AA", "E14 5AB")
    print_result("Postcode Journey", journey)
except Exception as e:
    print(f"❌ Error: {e}")

# ============================================================
# SCENARIO 5: "Are there any disruptions on the network?"
# ============================================================
print("\n" + "🚇"*30)
print("SCENARIO 5: Current Disruptions")
print("🚇"*30)

try:
    disruptions = tfl.get_disruptions("tube,dlr,overground,elizabeth-line")
    if disruptions:
        print_result("Active Disruptions", disruptions)
    else:
        print("✅ No disruptions currently!")
except Exception as e:
    print(f"❌ Error: {e}")

# ============================================================
# SCENARIO 6: "When's the next 73 bus?"
# ============================================================
print("\n" + "🚂"*30)
print("SCENARIO 6: Bus arrivals - Route 73")
print("🚂"*30)

try:
    # Search for a bus stop on route 73 (Victoria to Stoke Newington)
    bus_stops = tfl.search_bus_stops("Victoria Station")
    print_result("Bus stops near Victoria", bus_stops[:3])

    if bus_stops and bus_stops[0].get('id'):
        stop_id = bus_stops[0]['id']
        bus_arrivals = tfl.get_bus_arrivals(stop_id)
        print_result(f"Bus arrivals at {stop_id}", bus_arrivals[:5])
except Exception as e:
    print(f"❌ Error: {e}")

# ============================================================
# SCENARIO 7: "What stations are on the Elizabeth line?"
# ============================================================
print("\n" + "🚇"*30)
print("SCENARIO 7: Elizabeth Line Stations")
print("🚇"*30)

try:
    elizabeth_stops = tfl.get_line_stops("elizabeth")
    print(f"Found {len(elizabeth_stops)} stations on Elizabeth line")
    print_result("First 5 stations", elizabeth_stops[:5])
except Exception as e:
    print(f"❌ Error: {e}")

# ============================================================
# SCENARIO 8: Edge case - Misspelled station name
# ============================================================
print("\n" + "🚇"*30)
print("SCENARIO 8: Edge case - Misspelled 'Picadilly' (missing 'c')")
print("🚇"*30)

try:
    stops = tfl.search_stops("Picadilly Circus", "tube")
    print_result("Search results for misspelled name", stops)
except Exception as e:
    print(f"❌ Error: {e}")

# ============================================================
# SCENARIO 9: DLR + Overground status
# ============================================================
print("\n" + "🚇"*30)
print("SCENARIO 9: DLR and Overground Status")
print("🚇"*30)

try:
    status = tfl.get_line_status("dlr,overground")
    print_result("DLR + Overground Status", status)
except Exception as e:
    print(f"❌ Error: {e}")

# ============================================================
# SCENARIO 10: Find bus stops near coordinates (Trafalgar Square)
# ============================================================
print("\n" + "🚂"*30)
print("SCENARIO 10: Bus stops near Trafalgar Square (by coordinates)")
print("🚂"*30)

try:
    # Trafalgar Square coordinates
    bus_stops = tfl.search_bus_stops(lat=51.508039, lon=-0.128069, radius=200)
    print_result("Bus stops within 200m of Trafalgar Square", bus_stops)
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*60)
print("✅ Testing complete!")
print("="*60)

tfl.close()
