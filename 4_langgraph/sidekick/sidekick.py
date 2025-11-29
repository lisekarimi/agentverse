# sidekick.py
from typing import TypedDict, Annotated, List, Any, Optional, Dict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from pydantic import BaseModel, Field
from tools import get_all_tools
from datetime import datetime
import logging

# ========== LOGGING SETUP ==========
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# ========== STATE ==========
class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool

# ========== EVALUATOR OUTPUT MODEL ==========
class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(description="True if more input is needed from the user")

# ========== SIDEKICK CLASS ==========
class Sidekick:
    def __init__(self):
        logger.info("Initializing Sidekick...")
        self.tools = get_all_tools()
        logger.info(f"Loaded {len(self.tools)} tools: {[tool.name for tool in self.tools]}")

        # Worker LLM (with tools)
        logger.debug("Setting up worker LLM with tools")
        worker_llm = ChatOpenAI(model="gpt-4o-mini")
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)

        # Evaluator LLM (with structured output)
        logger.debug("Setting up evaluator LLM with structured output")
        evaluator_llm = ChatOpenAI(model="gpt-4o-mini")
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)

        # Memory setup (will be initialized in setup())
        self.memory = None
        self._memory_conn_string = "sidekick_memory.db"
        self.graph = None
        self.db_conn = None
        logger.info("Sidekick initialization complete")

    async def setup(self):
        """Async initialization for memory and graph"""
        import aiosqlite

        logger.info("Setting up Sidekick (memory and graph)...")

        # Create database connection (stays open!)
        logger.debug(f"Connecting to database: {self._memory_conn_string}")
        self.db_conn = await aiosqlite.connect(self._memory_conn_string)
        logger.info("Database connection established")

        # Create memory saver with the connection
        logger.debug("Creating memory saver")
        self.memory = AsyncSqliteSaver(self.db_conn)

        # Build graph
        logger.debug("Building graph...")
        self.graph = self.build_graph()
        logger.info("Sidekick setup complete - graph compiled and ready")

    # ========== WORKER NODE ==========
    def worker(self, state: State) -> Dict[str, Any]:
        """Worker agent that does the actual task"""
        logger.info("=== WORKER NODE: Starting work ===")
        logger.debug(f"State keys: {list(state.keys())}")
        logger.debug(f"Number of messages: {len(state.get('messages', []))}")
        logger.info(f"Success criteria: {state.get('success_criteria', 'N/A')}")

        has_feedback = bool(state.get("feedback_on_work"))
        if has_feedback:
            logger.info(f"Retry attempt - Previous feedback: {state['feedback_on_work'][:100]}...")
        else:
            logger.info("First attempt at this task")

        system_message = f"""You are a helpful AI assistant that can use tools to complete tasks.
You work on tasks until either:
1. The success criteria is met, OR
2. You need clarification from the user

Current date and time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

SUCCESS CRITERIA:
{state['success_criteria']}

INSTRUCTIONS:
- Use tools to accomplish the task
- Always save your final answer to a file called 'result.txt' in the workspace folder
- If you have a question, clearly state: "Question: [your question]"
- When done, provide your final answer clearly
"""

        # Add feedback if this is a retry
        if state.get("feedback_on_work"):
            system_message += f"""

PREVIOUS ATTEMPT FEEDBACK:
{state['feedback_on_work']}

Please improve based on this feedback.
"""

        # Prepare messages
        messages = state["messages"].copy()

        # Update or add system message
        found_system = False
        for msg in messages:
            if isinstance(msg, SystemMessage):
                msg.content = system_message
                found_system = True
                break

        if not found_system:
            messages = [SystemMessage(content=system_message)] + messages

        logger.debug(f"Invoking worker LLM with {len(messages)} messages")
        # Call LLM
        response = self.worker_llm_with_tools.invoke(messages)

        # Log response details
        has_tool_calls = hasattr(response, "tool_calls") and response.tool_calls
        if has_tool_calls:
            tool_names = [tc.get("name", "unknown") for tc in response.tool_calls]
            logger.info(f"Worker response: {len(tool_names)} tool call(s) - {tool_names}")
        else:
            response_preview = response.content[:200] if hasattr(response, "content") else str(response)[:200]
            logger.info(f"Worker response (text): {response_preview}...")

        logger.info("=== WORKER NODE: Complete ===")
        return {"messages": [response]}

    # ========== WORKER ROUTER ==========
    def worker_router(self, state: State) -> str:
        """Decides: use tools OR go to evaluator"""
        last_message = state["messages"][-1]

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            tool_names = [tc.get("name", "unknown") for tc in last_message.tool_calls]
            logger.info(f"WORKER ROUTER: Routing to TOOLS (calls: {tool_names})")
            return "tools"
        else:
            logger.info("WORKER ROUTER: Routing to EVALUATOR (no tool calls)")
            return "evaluator"

    # ========== EVALUATOR NODE ==========
    def evaluator(self, state: State) -> Dict[str, Any]:
        """Evaluator agent that judges quality"""
        logger.info("=== EVALUATOR NODE: Starting evaluation ===")

        last_response = state["messages"][-1].content
        logger.debug(f"Evaluating response (length: {len(str(last_response))} chars)")

        system_message = """You are an evaluator that judges if a task was completed successfully.
Assess the assistant's response based on the success criteria.
Provide feedback and decide if:
1. Success criteria is met
2. More user input is needed
"""

        # Format conversation history
        conversation = self.format_conversation(state["messages"])
        logger.debug(f"Conversation history: {len(conversation)} chars")

        user_message = f"""Evaluate this conversation:

{conversation}

SUCCESS CRITERIA:
{state['success_criteria']}

ASSISTANT'S FINAL RESPONSE:
{last_response}

Decide if the success criteria is met and if user input is needed.
"""

        logger.debug("Invoking evaluator LLM")
        # Call evaluator LLM
        eval_result = self.evaluator_llm_with_output.invoke([
            SystemMessage(content=system_message),
            HumanMessage(content=user_message)
        ])

        logger.info("EVALUATOR RESULT:")
        logger.info(f"  - Success criteria met: {eval_result.success_criteria_met}")
        logger.info(f"  - User input needed: {eval_result.user_input_needed}")
        logger.info(f"  - Feedback: {eval_result.feedback[:150]}...")
        logger.info("=== EVALUATOR NODE: Complete ===")

        return {
            "messages": [{"role": "assistant", "content": f"Evaluator: {eval_result.feedback}"}],
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed
        }

    # ========== EVALUATION ROUTER ==========
    def route_based_on_evaluation(self, state: State) -> str:
        """Decides: done OR retry"""
        if state["success_criteria_met"] or state["user_input_needed"]:
            reason = "success criteria met" if state["success_criteria_met"] else "user input needed"
            logger.info(f"EVALUATION ROUTER: Routing to END ({reason})")
            return "END"
        else:
            logger.info("EVALUATION ROUTER: Routing back to WORKER (retry needed)")
            return "worker"

    # ========== HELPER: FORMAT CONVERSATION ==========
    def format_conversation(self, messages: List[Any]) -> str:
        """Format messages for evaluator"""
        conversation = ""
        for msg in messages:
            if isinstance(msg, HumanMessage):
                conversation += f"User: {msg.content}\n"
            elif isinstance(msg, AIMessage):
                text = msg.content or "[Tool use]"
                conversation += f"Assistant: {text}\n"
        return conversation

    # ========== BUILD GRAPH ==========
    def build_graph(self):
        """Builds the LangGraph workflow"""
        logger.debug("Building graph structure...")
        graph_builder = StateGraph(State)

        # Add nodes
        logger.debug("Adding nodes: worker, tools, evaluator")
        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("evaluator", self.evaluator)

        # Add edges
        logger.debug("Adding edges and conditional routes")
        graph_builder.add_conditional_edges(
            "worker",
            self.worker_router,
            {"tools": "tools", "evaluator": "evaluator"}
        )
        graph_builder.add_edge("tools", "worker")
        graph_builder.add_conditional_edges(
            "evaluator",
            self.route_based_on_evaluation,
            {"worker": "worker", "END": END}
        )
        graph_builder.add_edge(START, "worker")

        # Compile with memory
        logger.debug("Compiling graph with memory checkpointer")
        compiled = graph_builder.compile(checkpointer=self.memory)
        logger.info("Graph built and compiled successfully")

        # Display Mermaid diagram
        try:
            mermaid_diagram = compiled.get_graph().draw_mermaid()
            print("\n" + "=" * 60)
            print("MERMAID DIAGRAM:")
            print("=" * 60)
            print(mermaid_diagram)
            print("=" * 60 + "\n")
            logger.info("Mermaid diagram displayed")
        except Exception as e:
            logger.warning(f"Could not generate Mermaid diagram: {e}")

        return compiled

    # ========== RUN TASK ==========
    async def run_task(self, message: str, success_criteria: str, thread_id: str):
        """Runs the graph for one task"""
        logger.info("=" * 60)
        logger.info(f"RUNNING TASK (thread_id: {thread_id})")
        logger.info(f"Message: {message[:100]}...")
        logger.info(f"Success criteria: {success_criteria[:100] if success_criteria else 'Default'}...")
        logger.info("=" * 60)

        config = {"configurable": {"thread_id": thread_id}}

        state = {
            "messages": [{"role": "user", "content": message}],
            "success_criteria": success_criteria or "Provide a clear and helpful answer",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False
        }

        logger.debug("Invoking graph with initial state")
        result = await self.graph.ainvoke(state, config=config)
        logger.debug(f"Graph execution complete. Final state keys: {list(result.keys())}")

        # Extract worker's answer and evaluator feedback
        num_messages = len(result["messages"])
        logger.debug(f"Total messages in result: {num_messages}")

        if num_messages >= 2:
            worker_response = result["messages"][-2].content
            evaluator_feedback = result["messages"][-1].content
        else:
            logger.warning(f"Unexpected message count: {num_messages}, using last message")
            worker_response = result["messages"][-1].content if num_messages > 0 else "No response"
            evaluator_feedback = "No evaluator feedback available"

        logger.info("=" * 60)
        logger.info(f"TASK COMPLETE (thread_id: {thread_id})")
        logger.info(f"Success: {result['success_criteria_met']}")
        logger.info(f"User input needed: {result.get('user_input_needed', False)}")
        logger.info(f"Worker response length: {len(str(worker_response))} chars")
        logger.info(f"Evaluator feedback length: {len(str(evaluator_feedback))} chars")
        logger.info("=" * 60)

        return {
            "response": worker_response,
            "feedback": evaluator_feedback,
            "success": result["success_criteria_met"]
        }
