"""
Comprehensive Edge Case Test Suite for TFL MCP Server
Tests all possible edge cases before deployment
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

results = {"passed": 0, "failed": 0, "tests": []}

def test(name, func, expected_behavior):
    """Run a test and record results."""
    global results
    try:
        result = func()

        # Determine if test passed based on expected behavior
        if expected_behavior == "should_return_data":
            passed = result and not (isinstance(result, dict) and result.get("error"))
        elif expected_behavior == "should_return_empty":
            passed = result == [] or result == {} or (isinstance(result, dict) and result.get("journeys") == [])
        elif expected_behavior == "should_return_error":
            passed = isinstance(result, dict) and result.get("error")
        elif expected_behavior == "should_not_crash":
            passed = True  # If we got here, it didn't crash
        elif expected_behavior == "should_return_list":
            passed = isinstance(result, list)
        elif expected_behavior == "should_return_options":
            passed = isinstance(result, dict) and (result.get("from_options") or result.get("to_options"))
        else:
            passed = result is not None

        status = "✅ PASS" if passed else "❌ FAIL"
        if passed:
            results["passed"] += 1
        else:
            results["failed"] += 1

        # Truncate result for display
        result_str = str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
        results["tests"].append({"name": name, "status": status, "result": result_str})
        print(f"{status}: {name}")

    except Exception as e:
        results["failed"] += 1
        results["tests"].append({"name": name, "status": "💥 ERROR", "result": str(e)})
        print(f"💥 ERROR: {name} - {e}")

print("=" * 70)
print("TFL MCP SERVER - COMPREHENSIVE EDGE CASE TEST SUITE")
print("=" * 70)

# ============================================================
# CATEGORY 1: JOURNEY PLANNING EDGE CASES
# ============================================================
print("\n📍 CATEGORY 1: JOURNEY PLANNING EDGE CASES")
print("-" * 50)

# 1.1 Same origin and destination
test(
    "Same origin and destination",
    lambda: tfl.get_journey("Victoria Station", "Victoria Station"),
    "should_not_crash"
)

# 1.2 Invalid/non-existent location
test(
    "Non-existent location",
    lambda: tfl.get_journey("Hogwarts Station", "Narnia"),
    "should_return_error"
)

# 1.3 Very long journey (edge to edge of London)
test(
    "Long journey (Heathrow to Epping)",
    lambda: tfl.get_journey("Heathrow Terminal 5", "Epping Station"),
    "should_return_data"
)

# 1.4 Very short journey (walking distance)
test(
    "Short journey (walking distance)",
    lambda: tfl.get_journey("Leicester Square Station", "Piccadilly Circus Station"),
    "should_return_data"
)

# 1.5 Postcode to station
test(
    "Postcode to station name",
    lambda: tfl.get_journey("EC1A 1BB", "Waterloo Station"),
    "should_return_data"
)

# 1.6 Station to postcode
test(
    "Station to postcode",
    lambda: tfl.get_journey("Bank Station", "W1A 1AA"),
    "should_return_data"
)

# 1.7 Coordinates input
test(
    "Coordinates to station",
    lambda: tfl.get_journey("51.5074,-0.1278", "King's Cross Station"),
    "should_return_data"
)

# 1.8 Coordinates to coordinates
test(
    "Coordinates to coordinates",
    lambda: tfl.get_journey("51.5074,-0.1278", "51.5031,-0.1132"),
    "should_return_data"
)

# 1.9 Station with apostrophe
test(
    "Station with apostrophe (King's Cross)",
    lambda: tfl.get_journey("King's Cross Station", "St. Paul's Station"),
    "should_return_data"
)

# 1.10 Ambiguous location name
test(
    "Ambiguous name (just 'Bank')",
    lambda: tfl.get_journey("Bank", "Liverpool Street"),
    "should_not_crash"
)

# 1.11 Empty string input
test(
    "Empty string origin",
    lambda: tfl.get_journey("", "Victoria Station"),
    "should_not_crash"
)

# 1.12 Numbers only
test(
    "Numbers only in location",
    lambda: tfl.get_journey("123", "456"),
    "should_not_crash"
)

# 1.13 Special characters
test(
    "Special characters in location",
    lambda: tfl.get_journey("Victoria & Albert Museum", "Natural History Museum"),
    "should_not_crash"
)

# 1.14 Mixed case
test(
    "Mixed case station name",
    lambda: tfl.get_journey("VICTORIA STATION", "waterloo station"),
    "should_return_data"
)

# 1.15 Partial station name
test(
    "Partial station name",
    lambda: tfl.get_journey("Victoria", "Waterloo"),
    "should_not_crash"
)

# 1.16 Airport journey
test(
    "Airport to central (Gatwick to London Bridge)",
    lambda: tfl.get_journey("Gatwick Airport", "London Bridge Station"),
    "should_return_data"
)

# ============================================================
# CATEGORY 2: ARRIVALS EDGE CASES
# ============================================================
print("\n📍 CATEGORY 2: ARRIVALS EDGE CASES")
print("-" * 50)

# 2.1 Valid tube station
test(
    "Valid tube station arrivals",
    lambda: tfl.get_arrivals("940GZZLUVIC"),  # Victoria
    "should_return_list"
)

# 2.2 Invalid stop ID
test(
    "Invalid stop ID",
    lambda: tfl.get_arrivals("INVALID123"),
    "should_not_crash"
)

# 2.3 Empty stop ID
test(
    "Empty stop ID",
    lambda: tfl.get_arrivals(""),
    "should_not_crash"
)

# 2.4 Major interchange (King's Cross)
test(
    "Major interchange (King's Cross)",
    lambda: tfl.get_arrivals("940GZZLUKSX"),
    "should_return_list"
)

# 2.5 Limit parameter - small
test(
    "Arrivals with limit=1",
    lambda: len(tfl.get_arrivals("940GZZLUVIC", limit=1)) <= 1,
    "should_not_crash"
)

# 2.6 Limit parameter - large
test(
    "Arrivals with limit=100",
    lambda: tfl.get_arrivals("940GZZLUVIC", limit=100),
    "should_return_list"
)

# 2.7 Limit parameter - zero
test(
    "Arrivals with limit=0",
    lambda: tfl.get_arrivals("940GZZLUVIC", limit=0),
    "should_not_crash"
)

# 2.8 Limit parameter - negative
test(
    "Arrivals with limit=-1",
    lambda: tfl.get_arrivals("940GZZLUVIC", limit=-1),
    "should_not_crash"
)

# 2.9 DLR station
test(
    "DLR station arrivals",
    lambda: tfl.get_arrivals("940GZZDLCAN"),  # Canary Wharf DLR
    "should_return_list"
)

# 2.10 Elizabeth line station
test(
    "Elizabeth line station arrivals",
    lambda: tfl.get_arrivals("910GPADTLL"),  # Paddington EL
    "should_not_crash"
)

# ============================================================
# CATEGORY 3: LINE STATUS EDGE CASES
# ============================================================
print("\n📍 CATEGORY 3: LINE STATUS EDGE CASES")
print("-" * 50)

# 3.1 All tube lines
test(
    "All tube lines status",
    lambda: tfl.get_line_status("tube"),
    "should_return_list"
)

# 3.2 Single mode
test(
    "Single mode (DLR)",
    lambda: tfl.get_line_status("dlr"),
    "should_return_list"
)

# 3.3 Multiple modes
test(
    "Multiple modes (tube,dlr,overground)",
    lambda: tfl.get_line_status("tube,dlr,overground"),
    "should_return_list"
)

# 3.4 Invalid mode
test(
    "Invalid mode",
    lambda: tfl.get_line_status("invalid_mode"),
    "should_not_crash"
)

# 3.5 Empty mode
test(
    "Empty mode string",
    lambda: tfl.get_line_status(""),
    "should_not_crash"
)

# 3.6 All supported modes
test(
    "All modes (tube,dlr,overground,elizabeth-line,tram)",
    lambda: tfl.get_line_status("tube,dlr,overground,elizabeth-line,tram"),
    "should_return_list"
)

# 3.7 National rail
test(
    "National rail status",
    lambda: tfl.get_line_status("national-rail"),
    "should_not_crash"
)

# 3.8 Bus mode (many lines)
test(
    "Bus mode status",
    lambda: tfl.get_line_status("bus"),
    "should_not_crash"
)

# ============================================================
# CATEGORY 4: SEARCH EDGE CASES
# ============================================================
print("\n📍 CATEGORY 4: STOP SEARCH EDGE CASES")
print("-" * 50)

# 4.1 Normal search
test(
    "Normal search (Oxford Circus)",
    lambda: tfl.search_stops("Oxford Circus"),
    "should_return_list"
)

# 4.2 Partial match
test(
    "Partial match (Oxf)",
    lambda: tfl.search_stops("Oxf"),
    "should_return_list"
)

# 4.3 Single character
test(
    "Single character search",
    lambda: tfl.search_stops("A"),
    "should_not_crash"
)

# 4.4 Empty search
test(
    "Empty search query",
    lambda: tfl.search_stops(""),
    "should_not_crash"
)

# 4.5 Very long search
test(
    "Very long search query",
    lambda: tfl.search_stops("A" * 100),
    "should_not_crash"
)

# 4.6 Special characters
test(
    "Special characters in search",
    lambda: tfl.search_stops("King's Cross & St Pancras"),
    "should_not_crash"
)

# 4.7 Numbers in search
test(
    "Numbers in search (Terminal 5)",
    lambda: tfl.search_stops("Terminal 5"),
    "should_return_list"
)

# 4.8 Unicode characters
test(
    "Unicode characters",
    lambda: tfl.search_stops("Café"),
    "should_not_crash"
)

# 4.9 SQL injection attempt (safety check)
test(
    "SQL injection attempt",
    lambda: tfl.search_stops("'; DROP TABLE stations; --"),
    "should_not_crash"
)

# 4.10 HTML injection attempt
test(
    "HTML injection attempt",
    lambda: tfl.search_stops("<script>alert('xss')</script>"),
    "should_not_crash"
)

# 4.11 Misspelling
test(
    "Misspelling (Picadilly without c)",
    lambda: tfl.search_stops("Picadilly"),
    "should_not_crash"
)

# 4.12 Different modes filter
test(
    "Search with bus mode only",
    lambda: tfl.search_stops("Victoria", "bus"),
    "should_return_list"
)

# 4.13 Non-existent station
test(
    "Non-existent station search",
    lambda: tfl.search_stops("Hogwarts Express Platform"),
    "should_not_crash"
)

# ============================================================
# CATEGORY 5: LINE STOPS EDGE CASES
# ============================================================
print("\n📍 CATEGORY 5: LINE STOPS EDGE CASES")
print("-" * 50)

# 5.1 Valid tube line
test(
    "Victoria line stops",
    lambda: tfl.get_line_stops("victoria"),
    "should_return_list"
)

# 5.2 DLR
test(
    "DLR stops",
    lambda: tfl.get_line_stops("dlr"),
    "should_return_list"
)

# 5.3 Elizabeth line
test(
    "Elizabeth line stops",
    lambda: tfl.get_line_stops("elizabeth"),
    "should_return_list"
)

# 5.4 Invalid line
test(
    "Invalid line ID",
    lambda: tfl.get_line_stops("invalid-line"),
    "should_not_crash"
)

# 5.5 Empty line ID
test(
    "Empty line ID",
    lambda: tfl.get_line_stops(""),
    "should_not_crash"
)

# 5.6 Overground line
test(
    "Overground line (liberty)",
    lambda: tfl.get_line_stops("liberty"),
    "should_not_crash"
)

# 5.7 Bus line
test(
    "Bus line stops (73)",
    lambda: tfl.get_line_stops("73"),
    "should_not_crash"
)

# ============================================================
# CATEGORY 6: DISRUPTIONS EDGE CASES
# ============================================================
print("\n📍 CATEGORY 6: DISRUPTIONS EDGE CASES")
print("-" * 50)

# 6.1 Tube disruptions
test(
    "Tube disruptions",
    lambda: tfl.get_disruptions("tube"),
    "should_not_crash"
)

# 6.2 All modes disruptions
test(
    "All modes disruptions",
    lambda: tfl.get_disruptions("tube,dlr,overground,elizabeth-line"),
    "should_not_crash"
)

# 6.3 Invalid mode
test(
    "Invalid mode disruptions",
    lambda: tfl.get_disruptions("invalid"),
    "should_not_crash"
)

# 6.4 Empty mode
test(
    "Empty mode disruptions",
    lambda: tfl.get_disruptions(""),
    "should_not_crash"
)

# ============================================================
# CATEGORY 7: BUS ROUTES EDGE CASES
# ============================================================
print("\n📍 CATEGORY 7: BUS ROUTES EDGE CASES")
print("-" * 50)

# 7.1 All bus routes
test(
    "All bus routes (no filter)",
    lambda: tfl.get_bus_routes(),
    "should_return_list"
)

# 7.2 Specific route number
test(
    "Specific route (73)",
    lambda: tfl.get_bus_routes("73"),
    "should_return_list"
)

# 7.3 Night bus
test(
    "Night bus route (N29)",
    lambda: tfl.get_bus_routes("N29"),
    "should_not_crash"
)

# 7.4 Non-existent route
test(
    "Non-existent route (999999)",
    lambda: tfl.get_bus_routes("999999"),
    "should_not_crash"
)

# 7.5 Empty filter
test(
    "Empty filter",
    lambda: tfl.get_bus_routes(""),
    "should_return_list"
)

# ============================================================
# CATEGORY 8: BUS STOPS SEARCH EDGE CASES
# ============================================================
print("\n📍 CATEGORY 8: BUS STOPS SEARCH EDGE CASES")
print("-" * 50)

# 8.1 Search by name
test(
    "Bus stop search by name",
    lambda: tfl.search_bus_stops("Oxford Street"),
    "should_return_list"
)

# 8.2 Search by coordinates
test(
    "Bus stop search by coordinates",
    lambda: tfl.search_bus_stops(lat=51.5074, lon=-0.1278, radius=200),
    "should_return_list"
)

# 8.3 Large radius
test(
    "Large radius (5000m)",
    lambda: tfl.search_bus_stops(lat=51.5074, lon=-0.1278, radius=5000),
    "should_return_list"
)

# 8.4 Small radius
test(
    "Small radius (10m)",
    lambda: tfl.search_bus_stops(lat=51.5074, lon=-0.1278, radius=10),
    "should_not_crash"
)

# 8.5 Zero radius
test(
    "Zero radius",
    lambda: tfl.search_bus_stops(lat=51.5074, lon=-0.1278, radius=0),
    "should_not_crash"
)

# 8.6 Invalid coordinates
test(
    "Invalid coordinates (out of range)",
    lambda: tfl.search_bus_stops(lat=999, lon=999, radius=500),
    "should_not_crash"
)

# 8.7 No parameters
test(
    "No parameters",
    lambda: tfl.search_bus_stops(),
    "should_not_crash"
)

# 8.8 Coordinates outside London
test(
    "Coordinates outside London (Paris)",
    lambda: tfl.search_bus_stops(lat=48.8566, lon=2.3522, radius=500),
    "should_not_crash"
)

# ============================================================
# CATEGORY 9: BUS ARRIVALS EDGE CASES
# ============================================================
print("\n📍 CATEGORY 9: BUS ARRIVALS EDGE CASES")
print("-" * 50)

# 9.1 Valid bus stop
test(
    "Valid bus stop arrivals",
    lambda: tfl.get_bus_arrivals("490000077E"),  # Near Victoria
    "should_not_crash"
)

# 9.2 Filter by line
test(
    "Bus arrivals filtered by line",
    lambda: tfl.get_bus_arrivals("490000077E", line="24"),
    "should_not_crash"
)

# 9.3 Invalid stop ID
test(
    "Invalid bus stop ID",
    lambda: tfl.get_bus_arrivals("INVALID"),
    "should_not_crash"
)

# 9.4 Empty stop ID
test(
    "Empty bus stop ID",
    lambda: tfl.get_bus_arrivals(""),
    "should_not_crash"
)

# 9.5 Non-existent line filter
test(
    "Non-existent line filter",
    lambda: tfl.get_bus_arrivals("490000077E", line="XYZ999"),
    "should_not_crash"
)

# 9.6 Tube station ID for bus arrivals
test(
    "Tube station ID for bus arrivals",
    lambda: tfl.get_bus_arrivals("940GZZLUVIC"),
    "should_not_crash"
)

# ============================================================
# CATEGORY 10: STRESS & BOUNDARY TESTS
# ============================================================
print("\n📍 CATEGORY 10: STRESS & BOUNDARY TESTS")
print("-" * 50)

# 10.1 Rapid successive calls
test(
    "Rapid successive calls (5x arrivals)",
    lambda: [tfl.get_arrivals("940GZZLUVIC") for _ in range(5)][-1],
    "should_return_list"
)

# 10.2 Very long station name search
test(
    "Very long query string",
    lambda: tfl.search_stops("A" * 500),
    "should_not_crash"
)

# 10.3 Maximum results
test(
    "Search returning many results",
    lambda: tfl.search_stops("Station"),
    "should_return_list"
)

# 10.4 Null bytes
test(
    "Null bytes in query",
    lambda: tfl.search_stops("Victoria\x00Station"),
    "should_not_crash"
)

# 10.5 Newlines in query
test(
    "Newlines in query",
    lambda: tfl.search_stops("Victoria\nStation"),
    "should_not_crash"
)

# ============================================================
# RESULTS SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("TEST RESULTS SUMMARY")
print("=" * 70)
print(f"✅ Passed: {results['passed']}")
print(f"❌ Failed: {results['failed']}")
print(f"📊 Total:  {results['passed'] + results['failed']}")
print(f"📈 Pass Rate: {results['passed'] / (results['passed'] + results['failed']) * 100:.1f}%")

if results['failed'] > 0:
    print("\n❌ FAILED TESTS:")
    for t in results['tests']:
        if t['status'] != "✅ PASS":
            print(f"  - {t['name']}: {t['result'][:100]}")

print("\n" + "=" * 70)

tfl.close()
