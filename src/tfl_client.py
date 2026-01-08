"""
TFL API Client for Transport for London data.
"""

import httpx
from typing import Optional
from datetime import datetime


class TFLClient:
    """Client for interacting with the TFL Unified API."""

    def __init__(self, api_key: str, base_url: str = "https://api.tfl.gov.uk"):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.Client(timeout=30.0)

    def _request(self, endpoint: str, params: Optional[dict] = None, follow_redirects: bool = True) -> dict | list:
        """Make an authenticated request to the TFL API."""
        if params is None:
            params = {}
        params["app_key"] = self.api_key

        url = f"{self.base_url}{endpoint}"

        try:
            response = self.client.get(url, params=params, follow_redirects=follow_redirects)
        except Exception as e:
            # Handle connection/timeout errors
            return {"_error": True, "error": f"Connection error: {str(e)}"}

        # Handle 300 Multiple Choices (disambiguation) - don't raise, return the response
        if response.status_code == 300:
            return {"_disambiguation": True, "_data": response.json()}

        # Handle common error status codes gracefully
        if response.status_code == 400:
            return {"_error": True, "error": "Invalid request - please check your input"}
        if response.status_code == 403:
            return {"_error": True, "error": "Request blocked - invalid characters in input"}
        if response.status_code == 404:
            return {"_error": True, "error": "Not found - location or stop does not exist"}

        try:
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"_error": True, "error": str(e)}

    # ==================== Line Status ====================

    def get_line_status(self, modes: str = "tube,dlr,overground,elizabeth-line") -> list[dict]:
        """
        Get current status of all lines for given modes.

        Args:
            modes: Comma-separated transport modes (e.g., "tube,dlr,overground")

        Returns:
            List of line statuses with disruption details
        """
        if not modes or not modes.strip():
            return [{"error": "Please specify at least one transport mode (e.g., tube, dlr, overground)"}]

        data = self._request(f"/Line/Mode/{modes}/Status")

        if isinstance(data, dict) and data.get("_error"):
            return [{"error": data.get("error", "Failed to get line status")}]

        return [self._normalize_line_status(line) for line in data]

    def _normalize_line_status(self, line: dict) -> dict:
        """Normalize line status response."""
        statuses = line.get("lineStatuses", [])
        current_status = statuses[0] if statuses else {}

        return {
            "id": line.get("id"),
            "name": line.get("name"),
            "mode": line.get("modeName"),
            "status": current_status.get("statusSeverityDescription", "Unknown"),
            "severity": current_status.get("statusSeverity", 0),
            "reason": current_status.get("reason"),
            "disruption_category": current_status.get("disruption", {}).get("category") if current_status.get("disruption") else None,
        }

    # ==================== Arrivals ====================

    def get_arrivals(self, stop_id: str, limit: int = 10) -> list[dict]:
        """
        Get real-time arrival predictions at a stop.

        Args:
            stop_id: The NaPTAN ID of the stop
            limit: Maximum number of arrivals to return

        Returns:
            List of upcoming arrivals sorted by time
        """
        if not stop_id or not stop_id.strip():
            return [{"error": "Please provide a valid stop ID. Use search_stops to find stop IDs."}]

        data = self._request(f"/StopPoint/{stop_id}/Arrivals")

        if isinstance(data, dict) and data.get("_error"):
            return [{"error": f"Could not find arrivals for stop '{stop_id}'. Please check the stop ID."}]

        arrivals = [self._normalize_arrival(arr) for arr in data]
        arrivals.sort(key=lambda x: x["time_to_arrival_seconds"])

        if limit <= 0:
            limit = 10

        return arrivals[:limit]

    def _normalize_arrival(self, arrival: dict) -> dict:
        """Normalize arrival prediction response."""
        return {
            "line": arrival.get("lineName"),
            "destination": arrival.get("destinationName"),
            "platform": arrival.get("platformName"),
            "direction": arrival.get("direction"),
            "time_to_arrival_seconds": arrival.get("timeToStation", 0),
            "time_to_arrival_minutes": round(arrival.get("timeToStation", 0) / 60, 1),
            "expected_arrival": arrival.get("expectedArrival"),
            "vehicle_id": arrival.get("vehicleId"),
            "mode": arrival.get("modeName"),
        }

    # ==================== Stop Search ====================

    def search_stops(self, query: str, modes: str = "tube,dlr,overground,elizabeth-line,bus") -> list[dict]:
        """
        Search for stops/stations by name.

        Args:
            query: Search query (station name)
            modes: Comma-separated transport modes to filter

        Returns:
            List of matching stops
        """
        if not query or not query.strip():
            return [{"error": "Please provide a search query (station or stop name)"}]

        # Sanitize query - remove potentially problematic characters
        query = query.replace('\x00', '').replace('\n', ' ').replace('\r', ' ').strip()

        if len(query) > 100:
            query = query[:100]

        params = {"modes": modes}
        data = self._request(f"/StopPoint/Search/{query}", params)

        if isinstance(data, dict) and data.get("_error"):
            return [{"error": data.get("error", f"Could not search for '{query}'")}]

        matches = data.get("matches", [])
        return [self._normalize_stop(stop) for stop in matches[:20]]

    def _normalize_stop(self, stop: dict) -> dict:
        """Normalize stop point response."""
        return {
            "id": stop.get("id") or stop.get("naptanId") or stop.get("icsId"),
            "name": stop.get("name") or stop.get("commonName"),
            "modes": stop.get("modes", []),
            "zone": stop.get("zone"),
            "lat": stop.get("lat"),
            "lon": stop.get("lon"),
            "lines": [line.get("name") for line in stop.get("lines", [])] if stop.get("lines") else [],
        }

    # ==================== Journey Planning ====================

    def get_journey(self, from_location: str, to_location: str) -> dict:
        """
        Plan a journey between two locations.

        Args:
            from_location: Starting point (station ID, postcode, or coordinates)
            to_location: Destination (station ID, postcode, or coordinates)

        Returns:
            Journey options with duration and steps
        """
        # Validate inputs
        if not from_location or not from_location.strip():
            return {"error": "Please provide a starting location", "journeys": []}
        if not to_location or not to_location.strip():
            return {"error": "Please provide a destination", "journeys": []}

        # Sanitize inputs
        from_location = from_location.replace('\x00', '').replace('\n', ' ').strip()
        to_location = to_location.replace('\x00', '').replace('\n', ' ').strip()

        # Check for same origin and destination
        if from_location.lower() == to_location.lower():
            return {"error": "Origin and destination are the same location", "journeys": []}

        data = self._request(f"/Journey/JourneyResults/{from_location}/to/{to_location}")

        # Handle API errors
        if isinstance(data, dict) and data.get("_error"):
            return {"error": data.get("error", "Could not plan journey"), "journeys": []}

        # Handle disambiguation (300 Multiple Choices)
        if isinstance(data, dict) and data.get("_disambiguation"):
            disambig_data = data.get("_data", {})

            # Extract disambiguation options
            from_options = disambig_data.get("fromLocationDisambiguation", {}).get("disambiguationOptions", [])
            to_options = disambig_data.get("toLocationDisambiguation", {}).get("disambiguationOptions", [])

            # If we have options, try to auto-resolve by picking the first station match
            from_id = None
            to_id = None

            if from_options:
                # Prefer stations/stops over other place types
                for opt in from_options:
                    place = opt.get("place", {})
                    if place.get("placeType") in ["StopPoint", "Station"]:
                        from_id = place.get("icsCode") or place.get("naptanId") or place.get("id")
                        break
                if not from_id and from_options:
                    place = from_options[0].get("place", {})
                    from_id = place.get("icsCode") or place.get("naptanId") or place.get("id")

            if to_options:
                for opt in to_options:
                    place = opt.get("place", {})
                    if place.get("placeType") in ["StopPoint", "Station"]:
                        to_id = place.get("icsCode") or place.get("naptanId") or place.get("id")
                        break
                if not to_id and to_options:
                    place = to_options[0].get("place", {})
                    to_id = place.get("icsCode") or place.get("naptanId") or place.get("id")

            # Retry with resolved IDs
            if from_id or to_id:
                resolved_from = from_id or from_location
                resolved_to = to_id or to_location
                return self.get_journey(resolved_from, resolved_to)

            # If we still can't resolve, return helpful error with options
            return {
                "error": "Ambiguous locations - please be more specific",
                "from_options": [
                    {
                        "name": opt.get("place", {}).get("commonName"),
                        "id": opt.get("place", {}).get("icsCode") or opt.get("place", {}).get("naptanId"),
                        "type": opt.get("place", {}).get("placeType"),
                    }
                    for opt in from_options[:5]
                ] if from_options else [],
                "to_options": [
                    {
                        "name": opt.get("place", {}).get("commonName"),
                        "id": opt.get("place", {}).get("icsCode") or opt.get("place", {}).get("naptanId"),
                        "type": opt.get("place", {}).get("placeType"),
                    }
                    for opt in to_options[:5]
                ] if to_options else [],
                "journeys": [],
            }

        journeys = data.get("journeys", [])

        if not journeys:
            return {"error": "No journeys found", "journeys": []}

        return {
            "from": data.get("fromLocationDisambiguation", {}).get("matchedStop", {}).get("name") or from_location,
            "to": data.get("toLocationDisambiguation", {}).get("matchedStop", {}).get("name") or to_location,
            "journeys": [self._normalize_journey(j) for j in journeys[:3]],
        }

    def _normalize_journey(self, journey: dict) -> dict:
        """Normalize journey response."""
        legs = journey.get("legs", [])
        return {
            "duration_minutes": journey.get("duration"),
            "arrival_time": journey.get("arrivalDateTime"),
            "departure_time": journey.get("startDateTime"),
            "legs": [
                {
                    "mode": leg.get("mode", {}).get("name"),
                    "from": leg.get("departurePoint", {}).get("commonName"),
                    "to": leg.get("arrivalPoint", {}).get("commonName"),
                    "duration_minutes": leg.get("duration"),
                    "line": leg.get("routeOptions", [{}])[0].get("name") if leg.get("routeOptions") else None,
                    "direction": leg.get("routeOptions", [{}])[0].get("direction") if leg.get("routeOptions") else None,
                    "instruction": leg.get("instruction", {}).get("summary"),
                }
                for leg in legs
            ],
        }

    # ==================== Line Stops ====================

    def get_line_stops(self, line_id: str) -> list[dict]:
        """
        Get all stops on a specific line.

        Args:
            line_id: Line identifier (e.g., "victoria", "elizabeth", "dlr")

        Returns:
            List of stops served by the line
        """
        if not line_id or not line_id.strip():
            return [{"error": "Please provide a line ID (e.g., victoria, central, dlr, elizabeth)"}]

        data = self._request(f"/Line/{line_id}/StopPoints")

        if isinstance(data, dict) and data.get("_error"):
            return [{"error": f"Could not find line '{line_id}'. Try: victoria, central, northern, jubilee, dlr, elizabeth"}]

        return [self._normalize_stop(stop) for stop in data]

    # ==================== Disruptions ====================

    def get_disruptions(self, modes: str = "tube,dlr,overground,elizabeth-line") -> list[dict]:
        """
        Get current disruptions across the network.

        Args:
            modes: Comma-separated transport modes

        Returns:
            List of active disruptions
        """
        if not modes or not modes.strip():
            return [{"error": "Please specify transport modes (e.g., tube, dlr, overground)"}]

        data = self._request(f"/Line/Mode/{modes}/Disruption")

        if isinstance(data, dict) and data.get("_error"):
            return [{"error": data.get("error", "Failed to get disruptions")}]

        return [self._normalize_disruption(d) for d in data]

    def _normalize_disruption(self, disruption: dict) -> dict:
        """Normalize disruption response."""
        return {
            "category": disruption.get("category"),
            "description": disruption.get("description"),
            "affected_routes": [
                {
                    "id": route.get("id"),
                    "name": route.get("name"),
                }
                for route in disruption.get("affectedRoutes", [])
            ],
            "affected_stops": [
                {
                    "id": stop.get("id"),
                    "name": stop.get("name"),
                }
                for stop in disruption.get("affectedStops", [])
            ],
            "closure_text": disruption.get("closureText"),
        }

    # ==================== Bus Routes ====================

    def get_bus_routes(self, query: Optional[str] = None) -> list[dict]:
        """
        Get all bus routes, optionally filtered by query.

        Args:
            query: Optional filter by route number or name

        Returns:
            List of bus routes
        """
        data = self._request("/Line/Mode/bus")
        routes = [
            {
                "id": line.get("id"),
                "name": line.get("name"),
                "mode": line.get("modeName"),
            }
            for line in data
        ]

        if query:
            query_lower = query.lower()
            routes = [r for r in routes if query_lower in r["id"].lower() or query_lower in r["name"].lower()]

        return routes[:50]  # Limit to 50 results

    # ==================== Bus Stops ====================

    def search_bus_stops(
        self,
        query: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        radius: int = 500,
    ) -> list[dict]:
        """
        Search for bus stops by name or location.

        Args:
            query: Search query (stop name)
            lat: Latitude for location-based search
            lon: Longitude for location-based search
            radius: Search radius in meters (default 500, max 2000)

        Returns:
            List of matching bus stops
        """
        if query:
            # Sanitize query
            query = query.replace('\x00', '').replace('\n', ' ').strip()
            if len(query) > 100:
                query = query[:100]

            # Search by name
            params = {"modes": "bus"}
            data = self._request(f"/StopPoint/Search/{query}", params)

            if isinstance(data, dict) and data.get("_error"):
                return [{"error": data.get("error", f"Could not search for '{query}'")}]

            matches = data.get("matches", [])
            return [self._normalize_stop(stop) for stop in matches[:20]]

        elif lat is not None and lon is not None:
            # Validate coordinates (roughly UK bounds)
            if not (49 < lat < 61 and -11 < lon < 3):
                return [{"error": "Coordinates must be within the UK. Please check latitude and longitude."}]

            # Limit radius to avoid timeouts (max 2000m)
            radius = max(50, min(radius, 2000))

            # Search by location
            params = {
                "stopTypes": "NaptanPublicBusCoachTram",
                "lat": lat,
                "lon": lon,
                "radius": radius,
            }
            data = self._request("/StopPoint", params)

            if isinstance(data, dict) and data.get("_error"):
                return [{"error": data.get("error", "Could not search for bus stops at this location")}]

            stops = data.get("stopPoints", [])
            return [self._normalize_stop(stop) for stop in stops[:20]]
        else:
            return [{"error": "Please provide either a search query or coordinates (lat/lon)"}]

    # ==================== Bus Arrivals ====================

    def get_bus_arrivals(self, stop_id: str, line: Optional[str] = None) -> list[dict]:
        """
        Get real-time bus arrivals at a stop.

        Args:
            stop_id: The NaPTAN ID of the bus stop
            line: Optional bus line filter

        Returns:
            List of upcoming bus arrivals
        """
        if not stop_id or not stop_id.strip():
            return [{"error": "Please provide a bus stop ID. Use search_bus_stops to find stop IDs."}]

        data = self._request(f"/StopPoint/{stop_id}/Arrivals")

        if isinstance(data, dict) and data.get("_error"):
            return [{"error": f"Could not find bus arrivals for stop '{stop_id}'. Please check the stop ID."}]

        arrivals = [self._normalize_arrival(arr) for arr in data if arr.get("modeName") == "bus"]

        if line:
            arrivals = [a for a in arrivals if a["line"] and line.lower() in a["line"].lower()]

        arrivals.sort(key=lambda x: x["time_to_arrival_seconds"])
        return arrivals[:15]

    def close(self):
        """Close the HTTP client."""
        self.client.close()
