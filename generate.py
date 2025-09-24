from agents import Agent, Runner
from dotenv import load_dotenv
import os
import json
import asyncio

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# Agent instructions: return the **entire adjacency list** as JSON
agent = Agent(
    name="Graph Generator",
    instructions="""
You are a graph generator for an emoji graph traversal game.
Generate a full emoji adjacency list where each emoji node lists all connected emojis.
All emojis must be relevant to each other (happy, sad, angry, surprised, etc.).
Return **ONLY valid JSON**, no explanations, markdown, or extra text.

Example output:
{
  "😀": ["😂", "😢", "😡"],
  "😂": ["😀", "😜", "🥲"],
  "😢": ["😀", "🥲", "😡"],
  "😡": ["😀", "😢", "😱"]
}
    """
)

async def call_graph_agent():
    return await Runner.run(agent, "Generate a full emoji graph adjacency list")

async def generate_graph():
    result = await call_graph_agent()
    # The structured output is in result.final_output, but it's often still a JSON string
    graph_json = result.final_output  # Could be a dict already
    if isinstance(graph_json, str):
        adjacency_list = json.loads(graph_json)
    else:
        adjacency_list = graph_json
    print("Generated graph:", adjacency_list)
    return adjacency_list

def get_children(emoji, adjacency_list):
    return adjacency_list.get(emoji, [])

async def test_get_children():
    adjacency_list = await generate_graph()
    print(get_children("😀", adjacency_list))
    print(get_children("😂", adjacency_list))

async def main():
    await test_get_children()

if __name__ == "__main__":
    asyncio.run(main())
