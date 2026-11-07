from openai import OpenAI

from src.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL


def main() -> None:
    client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

    print("Available models:")
    for model in client.models.list().data:
        print(" -", model.id)

    print(f"\nTesting model: {LLM_MODEL}")
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Answer in German."},
            {"role": "user", "content": "Erkläre in einem Satz, wofür ein Ersatzteil-Agent nützlich ist."},
        ],
        temperature=0,
    )

    print("\nAnswer:")
    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()