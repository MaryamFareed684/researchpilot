import groq

from app import config


class LLMError(Exception):
    """A problem talking to the LLM, with an HTTP status code for our API."""

    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


_client = None


def _get_client():
    global _client
    if _client is None:
        if not config.GROQ_API_KEY:
            raise LLMError(500, "GROQ_API_KEY is not set. Add it to backend/.env.")
        _client = groq.Groq(api_key=config.GROQ_API_KEY, timeout=30.0, max_retries=1)
    return _client


def generate(messages: list[dict]) -> str:
    """Send the messages to Groq and return the answer text."""
    extra = {"reasoning_effort": "low"} if "gpt-oss" in config.GROQ_MODEL else {}
    try:
        response = _get_client().chat.completions.create(
            model=config.GROQ_MODEL,
            messages=messages,
            temperature=config.LLM_TEMPERATURE,
            max_tokens=config.MAX_ANSWER_TOKENS,
            **extra,
        )
    except groq.RateLimitError:
        raise LLMError(429, "The free LLM limit was reached. Please wait a minute and try again.")
    except groq.AuthenticationError:
        raise LLMError(500, "The server's LLM key is invalid.")  # do not leak details
    except (groq.APIConnectionError, groq.APITimeoutError):
        raise LLMError(503, "Could not reach the LLM service. Try again.")
    except groq.APIStatusError as exc:
        raise LLMError(502, f"The LLM service returned an error ({exc.status_code}).")

    answer = (response.choices[0].message.content or "").strip()
    if not answer:
        raise LLMError(502, "The model returned an empty answer. Please try again.")
    return answer