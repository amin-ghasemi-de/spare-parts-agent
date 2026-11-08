import json
from typing import Literal

from pydantic import BaseModel

from src.config import LLM_MODEL
from src.extractor import extract_request
from src.llm_client import get_client
from src.schemas import SparePartRequest
from src.tools import check_stock, draft_reply, search_part_catalog

MAX_STEPS = 10

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_part_catalog",
            "description": (
                "Search the spare-parts catalog by part number or by part name (German or English). "
                "Returns candidate parts with a similarity score from 0 to 100. "
                "exact_part_no_match tells you whether the part number was found exactly."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Part number or part name to search for."},
                    "machine_model": {
                        "type": "string",
                        "description": "Optional machine model to filter compatible parts, e.g. HPC-300.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_stock",
            "description": "Check stock and delivery time for one catalog part number and a quantity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "part_no": {"type": "string", "description": "Exact part number from the catalog."},
                    "quantity": {"type": "integer", "description": "Requested quantity."},
                },
                "required": ["part_no", "quantity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draft_reply",
            "description": (
                "Create the reply draft for the customer. Prices, stock and delivery times are filled in "
                "automatically from the data. Only pass parts you have identified with certainty. "
                "Put everything that is unclear into open_questions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "contact_name": {"type": "string", "description": "Name of the person to address."},
                    "items": {
                        "type": "array",
                        "description": "Identified parts to offer.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "part_no": {"type": "string"},
                                "quantity": {"type": "integer"},
                            },
                            "required": ["part_no", "quantity"],
                        },
                    },
                    "open_questions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Questions to the customer, written in the reply language.",
                    },
                    "language": {"type": "string", "enum": ["de", "en"]},
                },
                "required": ["items", "language"],
            },
        },
    },
]

TOOL_FUNCTIONS = {
    "search_part_catalog": search_part_catalog,
    "check_stock": check_stock,
    "draft_reply": draft_reply,
}

SYSTEM_PROMPT = """You are the spare-parts assistant of an industrial equipment manufacturer.
You receive a customer e-mail and the data that was already extracted from it.

Your job:
1. For every requested item, find the part with search_part_catalog.
   Always pass machine_model if it is known.
   - If a part number is given, search for it first.
   - If exact_part_no_match is false, you MUST run a second search with the part name
     and the machine model. Never choose a part based only on a part-number search.
2. If several parts fit equally well and the e-mail does not say which one, do NOT guess.
   Leave that part out of the offer and ask the customer in open_questions which option they need.
3. If the customer wrote a part number and search_part_catalog returned exact_part_no_match = false,
   still offer the part you identified, but add an open question asking the customer to confirm it.
   Mention both part numbers in that question. If exact_part_no_match was true, do NOT ask:
   differences in spaces, hyphens or upper/lower case are the same part number.
4. Call check_stock for every identified part.
5. Call draft_reply exactly once. Use language "en" if the e-mail is in English, otherwise "de".
6. After draft_reply, answer with a short summary for the employee (2-4 sentences, English):
   what you identified, what is unclear, and what the employee should check.
   Report stock numbers exactly as check_stock returned them.
   Do not repeat the draft in the summary.

Rules for open_questions:
- Only ask for information you really need from the customer.
- Keep each question short. Do not repeat prices, stock or delivery times; the offer already shows them.
- Never mention stock quantities to the customer.
- Never promise anything (e.g. faster delivery or alternatives). The employee decides about that.

Never invent part numbers, prices or delivery times. Only use what the tools return."""

class ToolCallRecord(BaseModel):
    tool: str
    arguments: dict
    result: dict


class AgentResult(BaseModel):
    extraction: SparePartRequest
    trace: list[ToolCallRecord] = []
    draft: str | None = None
    summary: str | None = None
    steps_used: int = 0
    needs_attention: bool = False
    attention_reason: str | None = None
    status: Literal["finished", "not_a_request", "max_steps_reached"]


def _run_tool(name: str, arguments: dict) -> dict:
    function = TOOL_FUNCTIONS.get(name)
    if function is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return function(**arguments)
    except Exception as error:
        return {"error": f"{type(error).__name__}: {error}"}

def _check_attention(result: AgentResult) -> None:
    if result.extraction.urgency != "high":
        return
    missing = [
        record.result["part_no"]
        for record in result.trace
        if record.tool == "check_stock" and record.result.get("found") and not record.result["fully_available"]
    ]
    if missing:
        result.needs_attention = True
        result.attention_reason = f"Urgent request, but not fully in stock: {', '.join(sorted(set(missing)))}"


def run_agent(email_text: str) -> AgentResult:
    extraction = extract_request(email_text)
    if not extraction.is_spare_part_request:
        return AgentResult(extraction=extraction, status="not_a_request")

    client = get_client()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"E-mail:\n{email_text}\n\nExtracted data:\n{extraction.model_dump_json(indent=2)}",
        },
    ]
    result = AgentResult(extraction=extraction, status="max_steps_reached")

    for step in range(1, MAX_STEPS + 1):
        result.steps_used = step
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0,
        )
        message = response.choices[0].message

        if not message.tool_calls:
            result.summary = message.content
            result.status = "finished"
            break

        messages.append(
            {
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {"name": call.function.name, "arguments": call.function.arguments},
                    }
                    for call in message.tool_calls
                ],
            }
        )

        for call in message.tool_calls:
            try:
                arguments = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                arguments = {}
                tool_result = {"error": "Arguments were not valid JSON."}
            else:
                tool_result = _run_tool(call.function.name, arguments)

            result.trace.append(ToolCallRecord(tool=call.function.name, arguments=arguments, result=tool_result))
            if call.function.name == "draft_reply" and tool_result.get("ok"):
                result.draft = tool_result["draft"]

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(tool_result, ensure_ascii=False),
                }
            )
    _check_attention(result)
    return result