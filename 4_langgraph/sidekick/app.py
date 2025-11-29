# app.py
import gradio as gr
from sidekick import Sidekick
import uuid
import logging

# ========== LOGGING SETUP ==========
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# ========== INITIALIZE SIDEKICK ==========
sidekick = None

async def get_sidekick():
    """Get or create initialized sidekick"""
    global sidekick
    if sidekick is None:
        logger.info("Creating new Sidekick instance...")
        sidekick = Sidekick()
        await sidekick.setup()
        logger.info("Sidekick instance ready")
    else:
        logger.debug("Reusing existing Sidekick instance")
    return sidekick

# ========== HELPER FUNCTIONS ==========
def make_thread_id():
    """Generate unique thread ID for each conversation"""
    return str(uuid.uuid4())

async def process_message(message, success_criteria, history, thread_id):
    """Process user message through Sidekick"""
    logger.info(f"Processing message (thread_id: {thread_id})")
    logger.debug(f"Message: {message[:100]}...")
    logger.debug(f"Success criteria: {success_criteria[:100] if success_criteria else 'None'}...")
    logger.debug(f"History length: {len(history)} messages")

    if not message.strip():
        logger.warning("Empty message received, skipping")
        return history, thread_id

    # Get initialized sidekick
    sk = await get_sidekick()

    # Run Sidekick
    logger.info("Invoking Sidekick.run_task...")
    result = await sk.run_task(message, success_criteria, thread_id)
    logger.info(f"Sidekick returned: success={result['success']}")

    # Format for Gradio chat
    user_msg = {"role": "user", "content": message}
    assistant_msg = {"role": "assistant", "content": result["response"]}
    feedback_msg = {"role": "assistant", "content": result["feedback"]}

    new_history = history + [user_msg, assistant_msg, feedback_msg]
    logger.info(f"Message processing complete. New history length: {len(new_history)}")
    return new_history, thread_id

def reset():
    """Reset conversation with new thread ID"""
    new_thread_id = make_thread_id()
    logger.info(f"Resetting conversation. New thread_id: {new_thread_id}")
    return "", "", None, new_thread_id

# ========== GRADIO INTERFACE ==========
with gr.Blocks(title="Sidekick", theme=gr.themes.Default(primary_hue="emerald")) as demo:
    gr.Markdown("# 🤖 Sidekick - Your AI Assistant")
    gr.Markdown("Give me a task and define what success looks like!")

    # Hidden state for thread_id
    thread_id = gr.State(make_thread_id())

    # Chat interface
    with gr.Row():
        chatbot = gr.Chatbot(
            label="Conversation",
            height=400,
            type="messages"
        )

    # Input fields
    with gr.Group():
        with gr.Row():
            message = gr.Textbox(
                show_label=False,
                placeholder="Your task (e.g., 'Find 5 remote Data Scientist jobs')",
                scale=4
            )
        with gr.Row():
            success_criteria = gr.Textbox(
                show_label=False,
                placeholder="Success criteria (e.g., 'At least 5 jobs with links and company names')",
                scale=4
            )

    # Buttons
    with gr.Row():
        reset_btn = gr.Button("🔄 Reset", variant="secondary")
        submit_btn = gr.Button("🚀 Go!", variant="primary")

    # Examples
    gr.Examples(
        examples=[
            ["Find 5 remote Data Scientist jobs and send me the results by pushover", "At least 5 jobs with links and company names sent to pushover"],
            ["Find me some jobs", "Jobs that match my profile"],
            ["Send me job alerts", "Jobs I'd be interested in"],
        ],
        inputs=[message, success_criteria]
    )

    # Event handlers
    submit_btn.click(
        process_message,
        inputs=[message, success_criteria, chatbot, thread_id],
        outputs=[chatbot, thread_id]
    )

    message.submit(
        process_message,
        inputs=[message, success_criteria, chatbot, thread_id],
        outputs=[chatbot, thread_id]
    )

    success_criteria.submit(
        process_message,
        inputs=[message, success_criteria, chatbot, thread_id],
        outputs=[chatbot, thread_id]
    )

    reset_btn.click(
        reset,
        inputs=[],
        outputs=[message, success_criteria, chatbot, thread_id]
    )

# ========== LAUNCH ==========
if __name__ == "__main__":
    logger.info("Starting Gradio application...")
    demo.launch(inbrowser=True)
