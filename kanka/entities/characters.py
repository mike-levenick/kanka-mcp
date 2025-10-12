from mcp.server.fastmcp import FastMCP
from ..client import make_kanka_request, create_kanka_entity, update_kanka_entity

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

    @mcp.tool()
    async def create_character(
        name: str,
        entry: str = "",
        title: str = "",
        age: str = "",
        sex: str = "",
        pronouns: str = "",
        character_type: str = "",
        location_id: int = None,
        is_dead: bool = False,
        is_private: bool = False
    ) -> str:
        """Create a new character in the campaign.
        
        Args:
            name: The character's name (required)
            entry: HTML description of the character
            title: Character's title
            age: Character's age
            sex: Character's gender
            pronouns: Preferred pronouns
            character_type: Character type (e.g., "NPC", "PC", "Villain")
            location_id: ID of the character's location
            is_dead: Whether the character is deceased
            is_private: Whether the character is only visible to admins
        """
        character_data = {
            "name": name,
            "entry": entry,
            "title": title,
            "age": age,
            "sex": sex,
            "pronouns": pronouns,
            "type": character_type,
            "is_dead": is_dead,
            "is_private": is_private
        }
        
        # Only include location_id if provided
        if location_id is not None:
            character_data["location_id"] = location_id
        
        # Remove empty string values to keep the request clean
        character_data = {k: v for k, v in character_data.items() if v != ""}
        
        result = await create_kanka_entity("characters", character_data)
        
        if not result:
            return "Failed to create character."
        
        if "error" in result:
            return f"Error creating character: {result['error']}"
        
        if "data" in result:
            character = result["data"]
            return f"""
Successfully created character!

Name: {character.get('name')}
ID: {character.get('id')}
Title: {character.get('title') or 'None'}
Age: {character.get('age') or 'Unknown'}
Sex: {character.get('sex') or 'Unknown'}
Type: {character.get('type') or 'None'}
Location ID: {character.get('location_id') or 'None'}
Is Dead: {'Yes' if character.get('is_dead') else 'No'}
Visibility: {'Private' if character.get('is_private') else 'Public'}

The character has been added to your campaign.
"""
        
        return "Character created, but unexpected response format."

    @mcp.tool()
    async def update_character(
        character_name: str,
        entry: str = None,
        title: str = None,
        age: str = None,
        sex: str = None,
        pronouns: str = None,
        character_type: str = None,
        location_id: int = None,
        is_dead: bool = None,
        is_private: bool = None
    ) -> str:
        """Update an existing character by name.
        
        First searches for the character by name, then updates the specified fields.
        Only provided fields will be updated - others remain unchanged.
        
        Args:
            character_name: The name of the character to update (used for search)
            entry: HTML description of the character
            title: Character's title
            age: Character's age
            sex: Character's gender
            pronouns: Preferred pronouns
            character_type: Character type (e.g., "NPC", "PC", "Villain")
            location_id: ID of the character's location
            is_dead: Whether the character is deceased
            is_private: Whether the character is only visible to admins
        """
        # First, search for the character by name
        characters_data = await make_kanka_request("characters")
        
        if not characters_data or "data" not in characters_data:
            return f"Unable to search for character '{character_name}'."
        
        if "error" in characters_data:
            return f"Error searching for character: {characters_data['error']}"
        
        # Find character with matching name (case-insensitive)
        target_character = None
        for char in characters_data["data"]:
            if char.get("name", "").lower() == character_name.lower():
                target_character = char
                break
        
        if not target_character:
            return f"Character '{character_name}' not found in campaign."
        
        character_id = target_character["id"]
        
        # Build update data with only provided values
        update_data = {}
        if entry is not None:
            update_data["entry"] = entry
        if title is not None:
            update_data["title"] = title
        if age is not None:
            update_data["age"] = age
        if sex is not None:
            update_data["sex"] = sex
        if pronouns is not None:
            update_data["pronouns"] = pronouns
        if character_type is not None:
            update_data["type"] = character_type
        if location_id is not None:
            update_data["location_id"] = location_id
        if is_dead is not None:
            update_data["is_dead"] = is_dead
        if is_private is not None:
            update_data["is_private"] = is_private
        
        if not update_data:
            return "No updates provided. Please specify at least one field to update."
        
        # Update the character
        result = await update_kanka_entity(f"characters/{character_id}", update_data)
        
        if not result:
            return f"Failed to update character '{character_name}'."
        
        if "error" in result:
            return f"Error updating character: {result['error']}"
        
        if "data" in result:
            character = result["data"]
            updated_fields = list(update_data.keys())
            return f"""
Successfully updated character '{character_name}'!

Name: {character.get('name')}
ID: {character.get('id')}
Title: {character.get('title') or 'None'}
Age: {character.get('age') or 'Unknown'}
Sex: {character.get('sex') or 'Unknown'}
Type: {character.get('type') or 'None'}
Location ID: {character.get('location_id') or 'None'}
Is Dead: {'Yes' if character.get('is_dead') else 'No'}
Visibility: {'Private' if character.get('is_private') else 'Public'}

Updated fields: {', '.join(updated_fields)}
"""
        
        return "Character updated, but unexpected response format."