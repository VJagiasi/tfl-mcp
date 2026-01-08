# TFL MCP Server for Poke

A Model Context Protocol (MCP) server providing Transport for London data to AI assistants like Poke.

## Features

- **Real-time arrivals** at any Tube station or bus stop
- **Line status** for Tube, DLR, Overground, Elizabeth line
- **Journey planning** between any two locations
- **Service disruptions** and alerts
- **Bus routes** and bus stop search
- **All TFL modes** supported

## Tools Available

| Tool | Description |
|------|-------------|
| `get_arrivals` | Real-time arrivals at a station/stop |
| `get_line_status` | Current status of TFL lines |
| `search_stops` | Find stations by name |
| `plan_journey` | Journey planning between locations |
| `get_line_stops` | All stops on a specific line |
| `get_disruptions` | Active service disruptions |
| `get_bus_routes` | List London bus routes |
| `search_bus_stops` | Find bus stops by name or location |
| `get_bus_arrivals` | Real-time bus arrivals at a stop |

## Setup

### 1. Get a TFL API Key

1. Go to [api-portal.tfl.gov.uk/signup](https://api-portal.tfl.gov.uk/signup)
2. Create an account and verify your email
3. Subscribe to the "500 requests per minute" plan (free)
4. Copy your API key from your Profile

### 2. Local Development

```bash
# Clone the repository
git clone https://github.com/VJagiasi/tfl-mcp.git
cd tfl-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your TFL_API_KEY

# Run the server
python src/server.py
```

The server will start at `http://localhost:8000/mcp`

### 3. Test with MCP Inspector

```bash
# In another terminal
npx @anthropic/mcp-inspector
```

Open http://localhost:3000 and connect to `http://localhost:8000/mcp` using "Streamable HTTP" transport.

## Deployment to Render

### One-Click Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### Manual Deploy

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) and create a new Web Service
3. Connect your GitHub repository
4. Render will auto-detect `render.yaml`
5. Add environment variable: `TFL_API_KEY` = your API key
6. Deploy!

Your server will be available at: `https://tfl-mcp.onrender.com/mcp`

## Connect to Poke

1. Open Poke settings: [poke.com/settings/connections/integrations/new](https://poke.com/settings/connections/integrations/new)
2. Add MCP integration
3. Enter your server URL: `https://tfl-mcp.onrender.com/mcp`
4. Test it!

## Example Queries

Once connected to Poke, try asking:

- "What's the status of the Victoria line?"
- "When's the next train at King's Cross?"
- "Plan a journey from Paddington to Heathrow"
- "Are there any disruptions on the Tube?"
- "Find bus stops near Trafalgar Square"
- "When's the next 73 bus?"

## API Reference

This server uses the [TFL Unified API](https://api.tfl.gov.uk/). Key endpoints:

| Endpoint | Purpose |
|----------|---------|
| `/Line/Mode/{modes}/Status` | Line statuses |
| `/StopPoint/{id}/Arrivals` | Real-time arrivals |
| `/StopPoint/Search/{query}` | Search stations |
| `/Journey/JourneyResults/{from}/to/{to}` | Journey planning |

## License

MIT

## Disclaimer

This is not an official Transport for London (TFL) MCP server. It uses the publicly available TFL Unified API.
