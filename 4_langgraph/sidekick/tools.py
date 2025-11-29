# tools.py
from langchain.agents import Tool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.agent_toolkits import FileManagementToolkit
from dotenv import load_dotenv
import os
import re
import requests
import logging

# ========== LOGGING SETUP ==========
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

load_dotenv()

# ========== SERPER (Google Search) ==========
serper = GoogleSerperAPIWrapper()

def search_with_logging(query: str) -> str:
    """Wrapper for search tool with logging"""
    logger.info(f"🔍 SEARCH TOOL: Searching for '{query[:100]}...'")
    try:
        result = serper.run(query)
        logger.info(f"✅ SEARCH TOOL: Success. Result length: {len(str(result))} chars")
        logger.debug(f"Search result preview: {str(result)[:200]}...")
        return result
    except Exception as e:
        logger.error(f"❌ SEARCH TOOL: Error - {str(e)}")
        raise
search_tool = Tool(
    name="search",
    func=search_with_logging,
    description="Use this to search the web for information. Useful for finding job listings, company info, or any web research."
)

# ========== PUSHOVER (Push Notifications) ==========
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"

def send_push_notification(text: str) -> str:
    """Send a push notification to the user"""
    logger.info(f"📱 PUSHOVER TOOL: Sending notification (length: {len(text)} chars)")
    logger.debug(f"Notification preview: {text[:100]}...")

    # Convert Markdown to HTML
    # **bold** → <b>bold</b>
    html_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # *italic* → <i>italic</i>
    html_text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', html_text)

    try:
        response = requests.post(
            pushover_url,
            data={
                "token": pushover_token,
                "user": pushover_user,
                "message": html_text,
                "html": "1"  # Enable HTML formatting
            }
        )
        if response.status_code == 200:
            logger.info("✅ PUSHOVER TOOL: Notification sent successfully")
            return "Notification sent successfully"
        else:
            logger.warning(f"⚠️ PUSHOVER TOOL: Failed with status {response.status_code}")
            return f"Failed to send notification: {response.status_code}"
    except Exception as e:
        logger.error(f"❌ PUSHOVER TOOL: Error - {str(e)}")
        return f"Error sending notification: {str(e)}"

pushover_tool = Tool(
    name="send_push_notification",
    func=send_push_notification,
    description="Use this to send a push notification to the user with important updates or results"
)

# ========== FILE TOOLS ==========
def get_file_tools():
    logger.debug("Loading file management tools from workspace directory")
    toolkit = FileManagementToolkit(root_dir="workspace")  # Save files in workspace folder
    tools = toolkit.get_tools()
    logger.info(f"Loaded {len(tools)} file management tools")
    return tools

# ========== EXPORT ALL TOOLS ==========
def get_all_tools():
    logger.info("Getting all tools...")
    file_tools = get_file_tools()
    all_tools = [search_tool, pushover_tool] + file_tools
    logger.info(f"Total tools available: {len(all_tools)}")
    logger.debug(f"Tool names: {[tool.name for tool in all_tools]}")
    return all_tools
