# use_date_mcp.py
from dotenv import load_dotenv
from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio
import os
import asyncio
import gradio as gr

load_dotenv(override=True)

MODEL = "gpt-4o-mini"

# Date MCP Server params
date_params = {"command": "uv", "args": ["run", "date_server.py"]}

instructions = """
You are a date and appointment scheduling assistant for a clinic in Manhattan, New York, the United States (USA).
You have tools to:
- Get current date
- Parse natural language dates to standard format
- Calculate future/past dates
- Find specific weekdays
- Check if dates are business days (available for appointments)
- Check if dates are holidays

Always use your tools to provide accurate date information.
When checking appointment availability, verify the date is a business day and not a holiday.
"""

async def create_date_agent(task: str):
    # Create MCP client (subprocess)
    async with MCPServerStdio(params=date_params, client_session_timeout_seconds=30) as mcp_date:
        # Create agent with MCP client
        agent = Agent(
            name="date_assistant",
            instructions=instructions,
            model=MODEL,
            mcp_servers=[mcp_date]
        )
        # Run the agent
        with trace("date_query"):
            result = await Runner.run(agent, task)
            return result.final_output

def chat(message):
    """Wrapper function for Gradio"""
    result = asyncio.run(create_date_agent(message))
    return result

# Gradio Interface
if __name__ == "__main__":
    demo = gr.Interface(
        fn=chat,
        inputs=gr.Textbox(label="Ask about dates or appointments", placeholder="e.g., Is next Monday available?"),
        outputs=gr.Textbox(label="Response"),
        title="Clinic Appointment Assistant",
        description="Ask me about dates, availability, and appointment scheduling!"
    )

    demo.launch()
