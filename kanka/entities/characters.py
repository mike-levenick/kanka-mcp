from mcp.server.fastmcp import FastMCP
from ..client import make_kanka_request

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

def register_character_tools(mcp: FastMCP):
    """Register all character-related tools with the MCP server."""
    
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