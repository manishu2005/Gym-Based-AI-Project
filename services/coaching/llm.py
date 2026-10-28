import logging
from groq import APIStatusError, NotFoundError
from services.config.workout_config import PROMPT

logger = logging.getLogger(__name__)

DEFAULT_MODELS = [
    "qwen/qwen3.8-27b",
    "meta-llama/llama-prompt-guard-2-22m",
    "openai/gpt-oss-120b",
]


class LLMCoach:
    def __init__(self, groq_client, models=None):
        self.client = groq_client
        self.history = []
        self.system_prompt = PROMPT
        self.models = models or DEFAULT_MODELS

    def give_feedback(self, event: str, issue: str | None = None) -> str:
        prompt = f"Event: {event}"
        if issue:
            prompt += f" Form Issue: {issue}"

        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.history[-10:],
            {"role": "user", "content": prompt},
        ]

        last_error = None

        for model in self.models:
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.4,
                )

                text = response.choices[0].message.content.strip()

                self.history.append({"role": "user", "content": prompt})
                self.history.append({"role": "assistant", "content": text})

                self.history = self.history[-20:]
                return text

            except NotFoundError as err:
                logger.warning(
                    "Groq model '%s' not found (404). Falling back to next available model. Error: %s",
                    model,
                    err.message,
                )
                last_error = err
                continue

            except APIStatusError as err:
                logger.error(
                    "Groq API error on model '%s' (Status %s): %s",
                    model,
                    err.status_code,
                    err.message,
                )
                last_error = err
                continue

            except Exception as err:
                logger.exception("Unexpected error during LLM feedback generation: %s", err)
                last_error = err
                break

        # Fallback response if all API attempts fail so the voice pipeline does not crash
        logger.critical("All LLM models failed. Returning graceful fallback audio prompt.")
        return "Keep going, stay focused on your form."
