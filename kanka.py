from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# This assumes .env is in the same directory as kanka.py
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Initialize FastMCP server
mcp = FastMCP("kanka")

# Constants
KANKA_API_BASE = "https://api.kanka.io/1.0"

# Load from environment variables
KANKA_API_TOKEN = os.getenv("KANKA_API_TOKEN", "")
KANKA_CAMPAIGN_ID = os.getenv("KANKA_CAMPAIGN_ID", "")

async def make_kanka_request(endpoint: str) -> dict[str, Any] | None:
    """Make a request to the Kanka API with proper authentication and error handling."""
    headers = {
        "Authorization": f"Bearer {KANKA_API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    url = f"{KANKA_API_BASE}/campaigns/{KANKA_CAMPAIGN_ID}/{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except Exception as e:
            return {"error": str(e)}
        
async def create_kanka_entity(endpoint: str, data: dict[str, Any]) -> dict[str, Any] | None:
    """Create a new entity in Kanka via POST request."""
    headers = {
        "Authorization": f"Bearer {KANKA_API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    url = f"{KANKA_API_BASE}/campaigns/{KANKA_CAMPAIGN_ID}/{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=data, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except Exception as e:
            return {"error": str(e)}

def format_character_summary(char: dict) -> str:
    """Format a character into a readable summary."""
    return f"""
Name: {char.get('name', 'Unknown')}
ID: {char.get('id', 'N/A')}
Title: {char.get('title') or 'None'}
Age: {char.get('age') or 'Unknown'}
Sex: {char.get('sex') or 'Unknown'}
Type: {char.get('type') or 'None'}
Is Dead: {'Yes' if char.get('is_dead') else 'No'}
Location ID: {char.get('location_id') or 'None'}
Tags: {len(char.get('tags', []))} tag(s)
"""

def format_character_detail(char: dict) -> str:
    """Format a character's full details."""
    traits_text = ""
    if char.get('traits'):
        traits_text = "\n\nTraits:"
        for trait in char['traits']:
            traits_text += f"\n  - {trait.get('name')}: {trait.get('entry')}"
    
    return f"""
Name: {char.get('name', 'Unknown')}
ID: {char.get('id', 'N/A')}
Title: {char.get('title') or 'None'}
Age: {char.get('age') or 'Unknown'}
Sex: {char.get('sex') or 'Unknown'}
Pronouns: {char.get('pronouns') or 'None'}
Type: {char.get('type') or 'None'}
Is Dead: {'Yes' if char.get('is_dead') else 'No'}
Location ID: {char.get('location_id') or 'None'}

Entry/Description:
{char.get('entry', 'No description available.')}

Families: {char.get('families', [])}
Races: {char.get('races', [])}
Tags: {char.get('tags', [])}
{traits_text}
"""

@mcp.tool()
async def get_all_characters() -> str:
    """Get a list of all characters in the campaign.
    
    Returns a summary of all characters including their name, ID, and basic info.
    """
    data = await make_kanka_request("characters")
    
    if not data:
        return "Unable to fetch characters."
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    if "data" not in data or not data["data"]:
        return "No characters found in this campaign."
    
    characters = [format_character_summary(char) for char in data["data"]]
    return "\n---\n".join(characters)

@mcp.tool()
async def get_character(character_id: int) -> str:
    """Get detailed information about a specific character.
    
    Args:
        character_id: The ID of the character to retrieve
    """
    data = await make_kanka_request(f"characters/{character_id}")
    
    if not data:
        return f"Unable to fetch character with ID {character_id}."
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    if "data" not in data:
        return f"No character found with ID {character_id}."
    
    return format_character_detail(data["data"])

def format_journal_summary(journal: dict) -> str:
    """Format a journal into a readable summary."""
    return f"""
Name: {journal.get('name', 'Unknown')}
ID: {journal.get('id', 'N/A')}
Type: {journal.get('type') or 'None'}
Date: {journal.get('date') or 'No date'}
Author ID: {journal.get('author_id') or 'None'}
Calendar Date: {journal.get('calendar_year')}/{journal.get('calendar_month')}/{journal.get('calendar_day') if journal.get('calendar_year') else 'Not set'}
Parent Journal ID: {journal.get('journal_id') or 'None'}
Tags: {len(journal.get('tags', []))} tag(s)
Is Private: {'Yes' if journal.get('is_private') else 'No'}
"""

def format_journal_detail(journal: dict) -> str:
    """Format a journal's full details."""
    calendar_info = ""
    if journal.get('calendar_year'):
        calendar_info = f"\nCalendar Date: Year {journal.get('calendar_year')}, Month {journal.get('calendar_month')}, Day {journal.get('calendar_day')}"
        if journal.get('calendar_event_length'):
            calendar_info += f" (Duration: {journal.get('calendar_event_length')} days)"
    
    return f"""
Name: {journal.get('name', 'Unknown')}
ID: {journal.get('id', 'N/A')}
Type: {journal.get('type') or 'None'}
Date: {journal.get('date') or 'No date'}
Author ID: {journal.get('author_id') or 'None'}
Parent Journal ID: {journal.get('journal_id') or 'None (Top-level journal)'}
{calendar_info}

Entry/Content:
{journal.get('entry', 'No content available.')}

Tags: {journal.get('tags', [])}
Is Private: {'Yes' if journal.get('is_private') else 'No'}
Created: {journal.get('created_at')}
Last Updated: {journal.get('updated_at')}
"""

@mcp.tool()
async def get_all_journals() -> str:
    """Get a list of all journals in the campaign.
    
    Returns a summary of all journals including their name, ID, type, and date info.
    """
    data = await make_kanka_request("journals")
    
    if not data:
        return "Unable to fetch journals."
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    if "data" not in data or not data["data"]:
        return "No journals found in this campaign."
    
    journals = [format_journal_summary(journal) for journal in data["data"]]
    return "\n---\n".join(journals)

@mcp.tool()
async def get_journal(journal_id: int) -> str:
    """Get detailed information about a specific journal entry.
    
    Args:
        journal_id: The ID of the journal to retrieve
    """
    data = await make_kanka_request(f"journals/{journal_id}")
    
    if not data:
        return f"Unable to fetch journal with ID {journal_id}."
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    if "data" not in data:
        return f"No journal found with ID {journal_id}."
    
    return format_journal_detail(data["data"])

@mcp.tool()
async def create_session_recap(session_title: str, entry: str) -> str:
    """Create a new session recap journal entry under Campaign 2 Recaps.
    
    This tool specifically creates journal entries nested under the Campaign 2 Recaps
    parent journal (ID: 152961).
    
    Session titles should follow the format: "Session ## - Descriptive Title"
    For example: "Session 1 - The Beginning", "Session 43 - Into the Abyss"

    If unsure of the session number, ask for the session number before uploading.
    
    Args:
        session_title: The title/name of the session in format "Session ## - Title"
        entry: The HTML content of the session recap
    """
    # Campaign 2 Recaps parent journal ID
    CAMPAIGN_2_PARENT_ID = 152961
    
    journal_data = {
        "name": session_title,
        "entry": entry,
        "journal_id": CAMPAIGN_2_PARENT_ID,
        "type": "Recap",
        "is_private": False
    }
    
    result = await create_kanka_entity("journals", journal_data)
    
    if not result:
        return "Failed to create session recap."
    
    if "error" in result:
        return f"Error creating session recap: {result['error']}"
    
    if "data" in result:
        journal = result["data"]
        return f"""
Successfully created session recap!

Name: {journal.get('name')}
ID: {journal.get('id')}
Type: {journal.get('type')}
Parent Journal: Campaign 2 Recaps (ID: {CAMPAIGN_2_PARENT_ID})

The session recap has been added to your campaign.
"""
    
    return "Session recap created, but unexpected response format."

def main():
    import sys
    # Check if required env vars are set
    if not KANKA_API_TOKEN:
        print("ERROR: KANKA_API_TOKEN environment variable not set!", file=sys.stderr)
        return
    if not KANKA_CAMPAIGN_ID:
        print("ERROR: KANKA_CAMPAIGN_ID environment variable not set!", file=sys.stderr)
        return
    
    # Initialize and run the server
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()