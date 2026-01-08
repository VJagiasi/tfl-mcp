"""
TFL MCP Server for Poke

A Model Context Protocol server providing Transport for London data.
Supports Tube, DLR, Overground, Elizabeth line, Bus, and more.
"""

import os
from typing import Optional

from dotenv import load_dotenv
from fastmcp import FastMCP

from tfl_client import TFLClient

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP(
    "TFL MCP Server",
    instructions="""
    Use this server to get Transport for London (TFL) data including:
    - Real-time arrivals at any station or bus stop
    - Line status for Tube, DLR, Overground, and Elizabeth line
    - Journey planning between locations
    - Service disruptions and alerts
    - Bus routes and bus stop search

    Tips:
    - Use search_stops to find station IDs before getting arrivals
    - Line status gives you an overview of the entire network
    - Journey planning accepts station names, postcodes, or coordinates
    """,
)

# Initialize TFL client
api_key = os.environ.get("TFL_API_KEY", "")
if not api_key:
    print("Warning: TFL_API_KEY not set. API calls will fail.")

tfl = TFLClient(api_key=api_key)


# ==================== Core Tools (6) ====================


@mcp.tool(description="Get real-time arrival predictions at a TFL station or stop. Returns next trains/buses with times and destinations.")
def get_arrivals(stop_id: str, limit: int = 10) -> list[dict]:
    """
    Get real-time arrivals at a stop.

    Args:
        stop_id: The NaPTAN ID of the stop (use search_stops to find this)
        limit: Maximum number of arrivals to return (default 10)

    Returns:
        List of upcoming arrivals with line, destination, and time
    """
    try:
        return tfl.get_arrivals(stop_id, limit)
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool(description="Get current status of TFL lines (Tube, DLR, Overground, Elizabeth line) with any disruption details.")
def get_line_status(modes: str = "tube,dlr,overground,elizabeth-line") -> list[dict]:
    """
    Get status of all lines for given transport modes.

    Args:
        modes: Comma-separated transport modes. Options: tube, dlr, overground,
               elizabeth-line, tram, national-rail. Default covers main rail services.

    Returns:
        List of lines with status, severity, and disruption reason if any
    """
    try:
        return tfl.get_line_status(modes)
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool(description="Search for TFL stations and stops by name. Returns IDs needed for other tools like get_arrivals.")
def search_stops(query: str, modes: str = "tube,dlr,overground,elizabeth-line,bus") -> list[dict]:
    """
    Search for stops/stations by name.

    Args:
        query: Search query - station or stop name (e.g., "King's Cross", "Oxford Circus")
        modes: Comma-separated modes to filter. Default includes rail and bus.

    Returns:
        List of matching stops with IDs, names, zones, and lines served
    """
    try:
        return tfl.search_stops(query, modes)
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool(description="Plan a journey between two locations using TFL. Returns route options with duration and step-by-step directions. Use specific station names like 'King's Cross Station' or 'Heathrow Terminal 5' for best results.")
def plan_journey(from_location: str, to_location: str) -> dict:
    """
    Plan a journey between two locations.

    Args:
        from_location: Starting point - use specific names like "Victoria Station",
                      "Heathrow Terminal 5", postcodes (e.g., "SW1A 1AA"),
                      or coordinates (e.g., "51.5074,-0.1278")
        to_location: Destination - same format options as from_location

    Returns:
        Journey options with duration, departure/arrival times, and step-by-step legs
    """
    try:
        return tfl.get_journey(from_location, to_location)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description="Get all stops on a specific TFL line. Useful for finding stations served by a particular line.")
def get_line_stops(line_id: str) -> list[dict]:
    """
    Get all stops served by a specific line.

    Args:
        line_id: Line identifier. Examples:
                 - Tube: victoria, central, northern, piccadilly, jubilee, etc.
                 - DLR: dlr
                 - Overground: london-overground
                 - Elizabeth: elizabeth

    Returns:
        List of all stops on the line with names, IDs, and coordinates
    """
    try:
        return tfl.get_line_stops(line_id)
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool(description="Get current service disruptions across TFL network. Shows what's affected and closure details.")
def get_disruptions(modes: str = "tube,dlr,overground,elizabeth-line") -> list[dict]:
    """
    Get active disruptions across the network.

    Args:
        modes: Comma-separated transport modes to check

    Returns:
        List of active disruptions with category, description, and affected routes/stops
    """
    try:
        return tfl.get_disruptions(modes)
    except Exception as e:
        return [{"error": str(e)}]


# ==================== Bus Tools (3) ====================


@mcp.tool(description="Get all London bus routes, optionally filtered by route number or name.")
def get_bus_routes(query: Optional[str] = None) -> list[dict]:
    """
    Get bus routes in London.

    Args:
        query: Optional filter - route number (e.g., "73", "N29") or partial name

    Returns:
        List of bus routes with IDs and names
    """
    try:
        return tfl.get_bus_routes(query)
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool(description="Search for bus stops by name or find stops near a location using coordinates.")
def search_bus_stops(
    query: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius: int = 500,
) -> list[dict]:
    """
    Search for bus stops.

    Args:
        query: Search by stop name (e.g., "Trafalgar Square", "Oxford Street")
        lat: Latitude for location-based search (use with lon)
        lon: Longitude for location-based search (use with lat)
        radius: Search radius in meters when using lat/lon (default 500)

    Returns:
        List of bus stops with IDs, names, and locations
    """
    try:
        return tfl.search_bus_stops(query, lat, lon, radius)
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool(description="Get real-time bus arrivals at a specific bus stop, optionally filtered by bus line.")
def get_bus_arrivals(stop_id: str, line: Optional[str] = None) -> list[dict]:
    """
    Get upcoming bus arrivals at a stop.

    Args:
        stop_id: Bus stop NaPTAN ID (use search_bus_stops to find this)
        line: Optional bus line filter (e.g., "73", "N29")

    Returns:
        List of upcoming buses with line, destination, and time
    """
    try:
        return tfl.get_bus_arrivals(stop_id, line)
    except Exception as e:
        return [{"error": str(e)}]


# ==================== Server Entry Point ====================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"

    print(f"Starting TFL MCP Server on {host}:{port}")
    print(f"MCP endpoint: http://{host}:{port}/mcp")

    mcp.run(
        transport="streamable-http",
        host=host,
        port=port,
        stateless_http=True,
    )
