# backend/app/neptune_client.py

from gremlin_python.driver import client, serializer
import os

# Get the Neptune endpoint from an environment variable or hardcode for development.
NEPTUNE_ENDPOINT = os.getenv("NEPTUNE_ENDPOINT", "ws://localhost:8182/gremlin")

# Create a Gremlin client using GraphSON v2 serializer
gremlin_client = client.Client(NEPTUNE_ENDPOINT, 'g',
    message_serializer=serializer.GraphSONSerializersV3d0()
)

def run_query(query: str):
    """Submit a Gremlin query and return all results."""
    try:
        callback = gremlin_client.submit_async(query)
        if callback.result() is not None:
            return callback.result().all().result()
        return []
    except Exception as e:
        print(f"Error running query: {query}\nException: {e}")
        return []