# Phase 03: Extract Retry Logic from LLM Client

**Status:** ✅ COMPLETE
**Started:** 2026-02-11
**Completed:** 2026-02-11
**PR Title:** `refactor(llm): extract retry loop from generate_completion`
**Risk Level:** Low
**Estimated Effort:** Small (1-2 hours)
**Files Modified:** `llm/client.py`
**Dependencies:** None
**Blocks:** Phase 08

---

## Problem

`LLMClient.generate_completion()` (lines 261-404 in `llm/client.py`) mixes four concerns in one method at 4-5 levels of nesting:
1. Message preparation (lines 329-348)
2. Retry loop with exponential backoff (lines 352-400)
3. Provider-specific branching (Mock vs OpenAI) (lines 354-386)
4. Response construction (lines 362-386)

The retry loop is the main source of deep nesting and should be extracted to a private method.

---

## Implementation

### Step 1: Add `_execute_with_retry()` private method

Add this method to the `LLMClient` class **after** `_setup_client()` (after line 259) and **before** `generate_completion()` (line 261):

```python
    async def _execute_with_retry(self, params: dict) -> LLMResponse:
        """
        Execute an LLM API call with retry logic and exponential backoff.

        Args:
            params: Complete parameters dict for the API call (model, messages, etc.)

        Returns:
            LLMResponse with generated content and metadata

        Raises:
            LLMError: If all retry attempts fail
        """
        start_time = time.time()
        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                if self.config.provider == LLMProvider.MOCK:
                    response = await self._client.generate_completion(**params)
                    response_time = time.time() - start_time

                    logger.info(f"LLM Response (Mock) - Attempt: {attempt + 1}, Time: {response_time:.2f}s")
                    logger.debug(f"LLM Response Content: {response.content[:500]}...")

                    return LLMResponse(
                        content=response.content,
                        model=response.model,
                        usage=response.usage,
                        finish_reason=response.finish_reason,
                        response_time=response_time,
                        retry_count=attempt
                    )
                else:
                    response = await self._client.chat.completions.create(**params)

                response_time = time.time() - start_time
                content = response.choices[0].message.content

                logger.info(f"LLM Response (OpenAI) - Attempt: {attempt + 1}, Time: {response_time:.2f}s")
                logger.debug(f"LLM Response Content: {content[:500]}...")

                return LLMResponse(
                    content=content,
                    model=response.model,
                    usage=response.usage.dict() if response.usage else None,
                    finish_reason=response.choices[0].finish_reason,
                    response_time=response_time,
                    retry_count=attempt
                )

            except (openai.APIError, openai.APIConnectionError, openai.APITimeoutError,
                    openai.RateLimitError, openai.AuthenticationError) as e:
                last_error = e
                logger.warning(f"LLM call failed (attempt {attempt + 1}): {e}")

                if attempt < self.config.max_retries:
                    if "rate limit" in str(e).lower():
                        await asyncio.sleep(self.config.rate_limit_delay * (2 ** attempt))
                    else:
                        await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                else:
                    break

        response_time = time.time() - start_time
        raise LLMError(f"LLM call failed after {self.config.max_retries + 1} attempts: {last_error}")
```

### Step 2: Simplify `generate_completion()`

**Before** (lines 261-404 — the full method):
The method contains message preparation, parameter construction, and the entire retry loop inline.

**After:**
```python
    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate completion with comprehensive retry logic and error handling.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            system_prompt: Optional system prompt to prepend
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            LLMResponse with generated content and metadata

        Raises:
            LLMError: Base exception for LLM-related errors
            LLMRateLimitError: When rate limits are exceeded
            LLMTimeoutError: When requests timeout
            LLMValidationError: When response validation fails
        """
        # Prepare messages
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        logger.info(f"LLM Request - Provider: {self.config.provider.value}, Model: {self.config.model}")
        logger.debug(f"LLM Request Messages: {full_messages}")

        # Prepare parameters
        params = {
            "model": self.config.model,
            "messages": full_messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            **kwargs
        }

        logger.debug(f"LLM Request Parameters: {params}")

        return await self._execute_with_retry(params)
```

Note: The existing detailed docstring from the original `generate_completion()` can be trimmed to the shorter version above. The detailed parameter docs, examples, and performance notes from the original are excessive for a method that now delegates to `_execute_with_retry()`. However, if you want to preserve them, that's fine too — just keep the method signature and body as shown.

---

## Verification Checklist

1. Run LLM client tests:
   ```bash
   /Users/chris/Projects/30-day-abs/venv/bin/python3 -m pytest tests/llm/test_client.py -v
   ```

2. Run all LLM tests to catch indirect usage:
   ```bash
   /Users/chris/Projects/30-day-abs/venv/bin/python3 -m pytest tests/llm/ -v
   ```

3. Verify `generate_scenario()` still works (it calls `generate_completion()` internally):
   ```bash
   /Users/chris/Projects/30-day-abs/venv/bin/python3 -m pytest tests/llm/test_client.py -k "scenario" -v
   ```

4. Verify the public API of `LLMClient` is unchanged:
   - `generate_completion(messages, system_prompt, **kwargs)` — same signature
   - `generate_scenario(prompt, system_prompt, **kwargs)` — unchanged
   - `get_usage_stats()` — unchanged

5. Run broader tests:
   ```bash
   /Users/chris/Projects/30-day-abs/venv/bin/python3 -m pytest tests/ --ignore=tests/integration -x -q
   ```

---

## What NOT To Do

1. **Do NOT change the public API of `LLMClient`.** The method signature of `generate_completion()` must remain identical.

2. **Do NOT change the retry behavior.** The exponential backoff timing, rate limit detection, and max retry count must work exactly as before.

3. **Do NOT move `MockLLMClient` or `create_llm_client()`.** They stay where they are.

4. **Do NOT modify the exception types caught in the retry loop.** The tuple `(openai.APIError, openai.APIConnectionError, openai.APITimeoutError, openai.RateLimitError, openai.AuthenticationError)` is correct and must not change.

5. **Do NOT make `_execute_with_retry()` a standalone function.** It must be a method on `LLMClient` because it accesses `self.config` and `self._client`.

6. **Do NOT remove the verbose docstring if any tests assert on it.** Some test frameworks inspect docstrings. If in doubt, keep the original docstring.
