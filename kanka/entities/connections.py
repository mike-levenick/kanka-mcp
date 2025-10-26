from mcp.server.fastmcp import FastMCP
from ..client import make_kanka_request, create_kanka_entity, update_kanka_entity

# NOTE: In Kanka's API, these are called "relations" but in the GUI they are called "Connections"
# When working with these tools, "relation", "relations", and "connections" all refer to the same thing

def format_connection_summary(connection: dict) -> str:
    """Format a connection/relation into a readable summary."""
    attitude = connection.get('attitude')
    attitude_str = f"{attitude}" if attitude is not None else "Not set"

    return f"""
Relation: {connection.get('relation', 'Unknown')}
ID: {connection.get('id', 'N/A')}
Owner Entity ID: {connection.get('owner_id', 'N/A')}
Target Entity ID: {connection.get('target_id', 'N/A')}
Attitude: {attitude_str} (-100 to 100)
Two-Way: {'Yes' if connection.get('two_way') else 'No'}
Pinned: {'Yes' if connection.get('is_pinned') else 'No'}
Colour: {connection.get('colour') or 'None'}
"""

def format_connection_detail(connection: dict) -> str:
    """Format a connection/relation's full details."""
    attitude = connection.get('attitude')
    attitude_str = f"{attitude}" if attitude is not None else "Not set"

    visibility_map = {
        1: "All",
        2: "Self",
        3: "Admin",
        4: "Self & Admin",
        5: "Members"
    }
    visibility = visibility_map.get(connection.get('visibility_id'), "Unknown")

    return f"""
Relation: {connection.get('relation', 'Unknown')}
ID: {connection.get('id', 'N/A')}
Owner Entity ID: {connection.get('owner_id', 'N/A')}
Target Entity ID: {connection.get('target_id', 'N/A')}
Attitude: {attitude_str} (-100 to 100)
Colour: {connection.get('colour') or 'None'}
Two-Way: {'Yes' if connection.get('two_way') else 'No'}
Pinned: {'Yes' if connection.get('is_pinned') else 'No'}
Visibility: {visibility}
Created: {connection.get('created_at')}
Last Updated: {connection.get('updated_at')}
"""

def register_connection_tools(mcp: FastMCP):
    """Register all connection/relation-related tools with the MCP server.

    Note: In Kanka's API these are called "relations" but in the GUI they appear as "Connections".
    These tools use both terms interchangeably to match both the API and user expectations.
    """

    @mcp.tool()
    async def get_all_connections() -> str:
        """Get a list of all connections (relations) in the campaign.

        Note: In Kanka, connections are called "relations" in the API but "Connections" in the GUI.
        This retrieves all relationship links between entities in your campaign.

        Returns a summary of all connections including owner, target, relation type, and attitude.
        """
        data = await make_kanka_request("relations")

        if not data:
            return "Unable to fetch connections."

        if "error" in data:
            return f"Error: {data['error']}"

        if "data" not in data or not data["data"]:
            return "No connections found in this campaign."

        connections = [format_connection_summary(connection) for connection in data["data"]]
        return "\n---\n".join(connections)

    @mcp.tool()
    async def get_entity_connections(entity_id: int) -> str:
        """Get all connections (relations) for a specific entity.

        Note: In Kanka, connections are called "relations" in the API but "Connections" in the GUI.
        This retrieves all relationships where the specified entity is the owner.

        IMPORTANT: Use the ENTITY ID, not type-specific IDs (like character_id, location_id, etc.).

        Args:
            entity_id: The ENTITY ID to get connections for (not character_id, location_id, etc.)
        """
        data = await make_kanka_request(f"entities/{entity_id}/relations")

        if not data:
            return f"Unable to fetch connections for entity {entity_id}."

        if "error" in data:
            return f"Error: {data['error']}"

        if "data" not in data or not data["data"]:
            return f"No connections found for entity {entity_id}."

        connections = [format_connection_summary(connection) for connection in data["data"]]
        header = f"Connections for entity {entity_id}:\n\n"
        return header + "\n---\n".join(connections)

    @mcp.tool()
    async def get_connection(entity_id: int, connection_id: int) -> str:
        """Get detailed information about a specific connection (relation).

        Note: In Kanka, connections are called "relations" in the API but "Connections" in the GUI.

        IMPORTANT: Use the ENTITY ID, not type-specific IDs (like character_id, location_id, etc.).

        Args:
            entity_id: The owner ENTITY ID (not character_id, location_id, etc.)
            connection_id: The ID of the connection to retrieve
        """
        data = await make_kanka_request(f"entities/{entity_id}/relations/{connection_id}")

        if not data:
            return f"Unable to fetch connection {connection_id} for entity {entity_id}."

        if "error" in data:
            return f"Error: {data['error']}"

        if "data" not in data:
            return f"No connection found with ID {connection_id} for entity {entity_id}."

        return format_connection_detail(data["data"])

    @mcp.tool()
    async def create_connection(
        owner_id: int,
        target_id: int,
        relation: str,
        attitude: int = None,
        colour: str = None,
        two_way: bool = False,
        is_pinned: bool = False,
        visibility_id: int = 1
    ) -> str:
        """Create a new connection (relation) between two entities.

        Note: In Kanka, connections are called "relations" in the API but "Connections" in the GUI.
        This creates a relationship link from one entity to another.

        IMPORTANT: Connections use ENTITY IDs, not type-specific IDs (like character_id, location_id, etc.).
        Every entity in Kanka (characters, locations, creatures, etc.) has an entity_id.
        You must use the entity_id values for both owner_id and target_id.
        For example, to connect two characters, use their entity_id values, NOT their character id values.

        Args:
            owner_id: The source ENTITY ID (not character_id, location_id, etc.)
            target_id: The destination ENTITY ID (not character_id, location_id, etc.)
            relation: Description of the relationship (e.g., "Father of", "Enemy of", "Member of")
            attitude: Optional attitude score from -100 to 100 (negative=hostile, positive=friendly)
            colour: Optional hex color code for the connection (e.g., "#FF0000")
            two_way: If True, creates a bidirectional connection
            is_pinned: If True, shows the connection in the entity submenu
            visibility_id: Access level (1=All, 2=Self, 3=Admin, 4=Self&Admin, 5=Members)
        """
        connection_data = {
            "owner_id": owner_id,
            "target_id": target_id,
            "relation": relation,
            "two_way": two_way,
            "is_pinned": is_pinned,
            "visibility_id": visibility_id
        }

        # Only include optional fields if provided
        if attitude is not None:
            # Validate attitude range
            if attitude < -100 or attitude > 100:
                return "Error: Attitude must be between -100 and 100."
            connection_data["attitude"] = attitude

        if colour is not None:
            connection_data["colour"] = colour

        result = await create_kanka_entity(f"entities/{owner_id}/relations", connection_data)

        if not result:
            return "Failed to create connection."

        if "error" in result:
            return f"Error creating connection: {result['error']}"

        if "data" in result:
            # When two_way=True, the API returns a list of connections
            # Otherwise it returns a single connection object
            data = result["data"]

            if isinstance(data, list):
                # Two-way connection returns list of both directions
                if len(data) == 0:
                    return "Connection created but no data returned."

                # Show info about both connections
                connections_info = []
                for conn in data:
                    attitude_val = conn.get('attitude')
                    attitude_str = f"{attitude_val}" if attitude_val is not None else "Not set"
                    connections_info.append(f"""
Relation: {conn.get('relation')}
ID: {conn.get('id')}
Owner Entity ID: {conn.get('owner_id')}
Target Entity ID: {conn.get('target_id')}
Attitude: {attitude_str}
""")

                return f"""
Successfully created two-way connection!

{chr(10).join(connections_info)}
Pinned: {'Yes' if is_pinned else 'No'}

The bidirectional connection has been added to your campaign.
"""
            else:
                # Single connection
                connection = data
                attitude_val = connection.get('attitude')
                attitude_str = f"{attitude_val}" if attitude_val is not None else "Not set"

                return f"""
Successfully created connection!

Relation: {connection.get('relation')}
ID: {connection.get('id')}
Owner Entity ID: {connection.get('owner_id')}
Target Entity ID: {connection.get('target_id')}
Attitude: {attitude_str}
Two-Way: {'Yes' if connection.get('two_way') else 'No'}
Pinned: {'Yes' if connection.get('is_pinned') else 'No'}

The connection has been added to your campaign.
"""

        return "Connection created, but unexpected response format."

    @mcp.tool()
    async def update_connection(
        owner_id: int,
        connection_id: int,
        relation: str = None,
        target_id: int = None,
        attitude: int = None,
        colour: str = None,
        two_way: bool = None,
        is_pinned: bool = None,
        visibility_id: int = None
    ) -> str:
        """Update an existing connection (relation).

        Note: In Kanka, connections are called "relations" in the API but "Connections" in the GUI.
        Only provided fields will be updated - others remain unchanged.

        IMPORTANT: Connections use ENTITY IDs, not type-specific IDs (like character_id, location_id, etc.).
        Use entity_id values for owner_id and target_id parameters.

        Args:
            owner_id: The owner ENTITY ID containing the connection (not character_id, location_id, etc.)
            connection_id: The ID of the connection to update
            relation: New description of the relationship
            target_id: New target ENTITY ID (not character_id, location_id, etc.)
            attitude: New attitude score from -100 to 100
            colour: New hex color code for the connection
            two_way: New bidirectional setting
            is_pinned: New pinned status
            visibility_id: New access level (1=All, 2=Self, 3=Admin, 4=Self&Admin, 5=Members)
        """
        # Build update data with only provided values
        update_data = {}

        if relation is not None:
            update_data["relation"] = relation
        if target_id is not None:
            update_data["target_id"] = target_id
        if attitude is not None:
            # Validate attitude range
            if attitude < -100 or attitude > 100:
                return "Error: Attitude must be between -100 and 100."
            update_data["attitude"] = attitude
        if colour is not None:
            update_data["colour"] = colour
        if two_way is not None:
            update_data["two_way"] = two_way
        if is_pinned is not None:
            update_data["is_pinned"] = is_pinned
        if visibility_id is not None:
            update_data["visibility_id"] = visibility_id

        if not update_data:
            return "No updates provided. Please specify at least one field to update."

        # Update the connection
        result = await update_kanka_entity(f"entities/{owner_id}/relations/{connection_id}", update_data)

        if not result:
            return f"Failed to update connection {connection_id}."

        if "error" in result:
            return f"Error updating connection: {result['error']}"

        if "data" in result:
            connection = result["data"]
            updated_fields = list(update_data.keys())
            attitude_val = connection.get('attitude')
            attitude_str = f"{attitude_val}" if attitude_val is not None else "Not set"

            return f"""
Successfully updated connection!

Relation: {connection.get('relation')}
ID: {connection.get('id')}
Owner Entity ID: {connection.get('owner_id')}
Target Entity ID: {connection.get('target_id')}
Attitude: {attitude_str}
Two-Way: {'Yes' if connection.get('two_way') else 'No'}
Pinned: {'Yes' if connection.get('is_pinned') else 'No'}

Updated fields: {', '.join(updated_fields)}
"""

        return "Connection updated, but unexpected response format."
