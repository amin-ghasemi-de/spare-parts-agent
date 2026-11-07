import json

from pydantic import ValidationError

from src.config import LLM_MODEL
from src.llm_client import get_client
from src.schemas import SparePartRequest

SYSTEM_PROMPT = """You extract structured data from customer e-mails sent to the spare-parts service of an industrial equipment manufacturer.

Rules:
- Only use information that is written in the e-mail. Never invent or guess values.
- Copy part numbers exactly as written, even if they look wrong. Do not correct them.
- If a value is not mentioned, use null.
- Create one entry in "items" for each requested part.
- Answer with a single JSON object that matches this JSON schema:

{schema}
"""


def extract_request(email_text: str) -> SparePartRequest:
    schema = json.dumps(SparePartRequest.model_json_schema(), indent=2)
    client = get_client()

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.format(schema=schema)},
            {"role": "user", "content": email_text},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    raw_json = response.choices[0].message.content
    try:
        return SparePartRequest.model_validate_json(raw_json)
    except ValidationError as error:
        raise ValueError(f"LLM output does not match the schema:\n{raw_json}") from error