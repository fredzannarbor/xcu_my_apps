LLM Integration API
===================

This section documents the LLM integration layer that provides abstraction over different language model providers.

LLMCaller
---------

.. autoclass:: arxiv_writer.llm.caller.LLMCaller
   :members:
   :undoc-members:
   :show-inheritance:

   The main interface for interacting with Language Learning Models. Provides a unified API
   across different providers with built-in retry logic and error handling.

   **Example Usage:**

   .. code-block:: python

      from arxiv_writer.llm import LLMCaller, LLMConfig

      config = LLMConfig(
          provider="openai",
          model="gpt-4",
          temperature=0.7
      )
      
      caller = LLMCaller(config)
      
      messages = [
          {"role": "system", "content": "You are an academic writer."},
          {"role": "user", "content": "Write an introduction about machine learning."}
      ]
      
      response = caller.call_llm(messages)
      print(response.content)

EnhancedLLMCaller
-----------------

.. autoclass:: arxiv_writer.llm.enhanced_caller.EnhancedLLMCaller
   :members:
   :undoc-members:
   :show-inheritance:

   Enhanced version of LLMCaller with additional features like provider fallback,
   response caching, and advanced retry strategies.

   **Example Usage:**

   .. code-block:: python

      from arxiv_writer.llm import EnhancedLLMCaller

      config = {
          "providers": [
              {"provider": "openai", "model": "gpt-4", "priority": 1},
              {"provider": "anthropic", "model": "claude-3-sonnet", "priority": 2}
          ],
          "fallback_enabled": True,
          "cache_responses": True
      }
      
      caller = EnhancedLLMCaller(config)
      response = caller.call_llm_with_fallback(messages)

Data Models
-----------

LLMConfig
~~~~~~~~~

.. autoclass:: arxiv_writer.llm.models.LLMConfig
   :members:
   :undoc-members:
   :show-inheritance:

   Configuration class for LLM integration settings.

   **Attributes:**

   - ``provider`` (str): LLM provider name (e.g., "openai", "anthropic")
   - ``model`` (str): Specific model to use
   - ``temperature`` (float): Sampling temperature (0.0-2.0)
   - ``max_tokens`` (int): Maximum tokens per request
   - ``api_key`` (str): API key for the provider
   - ``api_base`` (str): Custom API endpoint URL
   - ``timeout`` (int): Request timeout in seconds
   - ``retry_config`` (RetryConfig): Retry configuration
   - ``rate_limit_config`` (RateLimitConfig): Rate limiting settings

LLMResponse
~~~~~~~~~~~

.. autoclass:: arxiv_writer.llm.models.LLMResponse
   :members:
   :undoc-members:
   :show-inheritance:

   Response object from LLM API calls.

   **Attributes:**

   - ``content`` (str): Generated text content
   - ``model`` (str): Model used for generation
   - ``token_usage`` (TokenUsage): Token usage statistics
   - ``finish_reason`` (str): Reason for completion
   - ``response_time`` (float): Response time in seconds
   - ``provider`` (str): Provider used for generation

Message
~~~~~~~

.. autoclass:: arxiv_writer.llm.models.Message
   :members:
   :undoc-members:
   :show-inheritance:

   Message object for LLM conversations.

   **Attributes:**

   - ``role`` (str): Message role ("system", "user", "assistant")
   - ``content`` (str): Message content
   - ``name`` (Optional[str]): Optional name for the message sender

TokenUsage
~~~~~~~~~~

.. autoclass:: arxiv_writer.llm.models.TokenUsage
   :members:
   :undoc-members:
   :show-inheritance:

   Token usage statistics from LLM API calls.

   **Attributes:**

   - ``input_tokens`` (int): Number of input tokens
   - ``output_tokens`` (int): Number of output tokens
   - ``total_tokens`` (int): Total tokens used
   - ``cost`` (Optional[float]): Estimated cost in USD

Provider Classes
----------------

BaseProvider
~~~~~~~~~~~~

.. autoclass:: arxiv_writer.llm.providers.base.BaseProvider
   :members:
   :undoc-members:
   :show-inheritance:

   Abstract base class for all LLM providers.

   **Methods to Implement:**

   .. code-block:: python

      class CustomProvider(BaseProvider):
          def call_llm(self, messages: List[Message], **kwargs) -> LLMResponse:
              # Implement provider-specific logic
              pass
          
          def get_available_models(self) -> List[str]:
              # Return list of available models
              pass
          
          def validate_config(self, config: LLMConfig) -> bool:
              # Validate provider-specific configuration
              pass

OpenAIProvider
~~~~~~~~~~~~~~

.. autoclass:: arxiv_writer.llm.providers.openai.OpenAIProvider
   :members:
   :undoc-members:
   :show-inheritance:

   OpenAI GPT provider implementation.

   **Supported Models:**
   - gpt-4
   - gpt-4-turbo
   - gpt-3.5-turbo
   - gpt-3.5-turbo-16k

   **Example Configuration:**

   .. code-block:: python

      config = LLMConfig(
          provider="openai",
          model="gpt-4",
          api_key="sk-...",
          temperature=0.7,
          max_tokens=2000
      )

AnthropicProvider
~~~~~~~~~~~~~~~~~

.. autoclass:: arxiv_writer.llm.providers.anthropic.AnthropicProvider
   :members:
   :undoc-members:
   :show-inheritance:

   Anthropic Claude provider implementation.

   **Supported Models:**
   - claude-3-opus-20240229
   - claude-3-sonnet-20240229
   - claude-3-haiku-20240307

   **Example Configuration:**

   .. code-block:: python

      config = LLMConfig(
          provider="anthropic",
          model="claude-3-sonnet-20240229",
          api_key="sk-ant-...",
          temperature=0.7,
          max_tokens=2000
      )

GoogleProvider
~~~~~~~~~~~~~~

.. autoclass:: arxiv_writer.llm.providers.google.GoogleProvider
   :members:
   :undoc-members:
   :show-inheritance:

   Google Gemini provider implementation.

   **Supported Models:**
   - gemini-pro
   - gemini-pro-vision

   **Example Configuration:**

   .. code-block:: python

      config = LLMConfig(
          provider="google",
          model="gemini-pro",
          api_key="AIza...",
          temperature=0.7
      )

Utility Classes
---------------

RetryHandler
~~~~~~~~~~~~

.. autoclass:: arxiv_writer.llm.retry.RetryHandler
   :members:
   :undoc-members:
   :show-inheritance:

   Handles retry logic with exponential backoff for LLM API calls.

   **Example Usage:**

   .. code-block:: python

      from arxiv_writer.llm.retry import RetryHandler, RetryConfig

      retry_config = RetryConfig(
          max_attempts=3,
          base_delay=1.0,
          max_delay=60.0,
          exponential_base=2.0
      )
      
      retry_handler = RetryHandler(retry_config)
      
      def api_call():
          # Your API call logic
          return provider.call_llm(messages)
      
      response = retry_handler.execute(api_call)

TokenUsageTracker
~~~~~~~~~~~~~~~~~

.. autoclass:: arxiv_writer.llm.token_usage_tracker.TokenUsageTracker
   :members:
   :undoc-members:
   :show-inheritance:

   Tracks token usage and costs across multiple LLM calls.

   **Example Usage:**

   .. code-block:: python

      from arxiv_writer.llm import TokenUsageTracker

      tracker = TokenUsageTracker()
      
      # Track usage from LLM responses
      tracker.add_usage(response.token_usage, response.model)
      
      # Get usage summary
      summary = tracker.get_summary()
      print(f"Total tokens: {summary.total_tokens}")
      print(f"Estimated cost: ${summary.total_cost:.2f}")

Configuration Classes
---------------------

RetryConfig
~~~~~~~~~~~

.. autoclass:: arxiv_writer.llm.models.RetryConfig
   :members:
   :undoc-members:
   :show-inheritance:

   Configuration for retry behavior.

   **Attributes:**

   - ``max_attempts`` (int): Maximum number of retry attempts
   - ``base_delay`` (float): Base delay between retries in seconds
   - ``max_delay`` (float): Maximum delay between retries
   - ``exponential_base`` (float): Base for exponential backoff
   - ``jitter`` (bool): Whether to add random jitter to delays

RateLimitConfig
~~~~~~~~~~~~~~~

.. autoclass:: arxiv_writer.llm.models.RateLimitConfig
   :members:
   :undoc-members:
   :show-inheritance:

   Configuration for rate limiting.

   **Attributes:**

   - ``requests_per_minute`` (int): Maximum requests per minute
   - ``tokens_per_minute`` (int): Maximum tokens per minute
   - ``requests_per_day`` (int): Maximum requests per day
   - ``tokens_per_day`` (int): Maximum tokens per day

Exception Classes
-----------------

.. automodule:: arxiv_writer.llm.exceptions
   :members:
   :undoc-members:
   :show-inheritance:

   **Exception Hierarchy:**

   - ``LLMError`` - Base LLM exception
     - ``ProviderError`` - Provider-specific errors
     - ``AuthenticationError`` - API key or authentication issues
     - ``RateLimitError`` - Rate limiting errors
     - ``ModelNotFoundError`` - Model not available
     - ``TokenLimitError`` - Token limit exceeded
     - ``TimeoutError`` - Request timeout

   **Example Usage:**

   .. code-block:: python

      from arxiv_writer.llm.exceptions import RateLimitError, AuthenticationError

      try:
          response = caller.call_llm(messages)
      except RateLimitError as e:
          print(f"Rate limit exceeded: {e}")
          # Implement backoff strategy
      except AuthenticationError as e:
          print(f"Authentication failed: {e}")
          # Check API key

Utility Functions
-----------------

.. automodule:: arxiv_writer.llm.utils
   :members: estimate_tokens, calculate_cost, validate_messages
   :undoc-members:

   **Utility Functions:**

   .. autofunction:: arxiv_writer.llm.utils.estimate_tokens

      Estimate token count for text content.

      **Parameters:**

      - ``text`` (str): Text to estimate tokens for
      - ``model`` (str): Model to use for estimation

      **Returns:**

      - ``int``: Estimated token count

   .. autofunction:: arxiv_writer.llm.utils.calculate_cost

      Calculate estimated cost for token usage.

      **Parameters:**

      - ``token_usage`` (TokenUsage): Token usage statistics
      - ``model`` (str): Model used for generation

      **Returns:**

      - ``float``: Estimated cost in USD

   .. autofunction:: arxiv_writer.llm.utils.validate_messages

      Validate message format for LLM calls.

      **Parameters:**

      - ``messages`` (List[Message]): Messages to validate

      **Returns:**

      - ``bool``: True if messages are valid

      **Raises:**

      - ``ValidationError``: If messages are invalid

Constants
---------

.. automodule:: arxiv_writer.llm.constants
   :members:
   :undoc-members:

   **Available Constants:**

   - ``SUPPORTED_PROVIDERS`` - List of supported LLM providers
   - ``DEFAULT_MODELS`` - Default models for each provider
   - ``TOKEN_LIMITS`` - Token limits by model
   - ``PRICING`` - Pricing information by model
   - ``RETRY_DEFAULTS`` - Default retry configuration

   **Example Usage:**

   .. code-block:: python

      from arxiv_writer.llm.constants import SUPPORTED_PROVIDERS, DEFAULT_MODELS

      print(f"Supported providers: {SUPPORTED_PROVIDERS}")
      print(f"Default OpenAI model: {DEFAULT_MODELS['openai']}")

Advanced Usage
--------------

Custom Provider Implementation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from arxiv_writer.llm.providers.base import BaseProvider
   from arxiv_writer.llm.models import LLMResponse, Message

   class CustomProvider(BaseProvider):
       """Custom LLM provider implementation."""
       
       def __init__(self, config: LLMConfig):
           super().__init__(config)
           # Initialize custom provider
       
       def call_llm(self, messages: List[Message], **kwargs) -> LLMResponse:
           """Implement custom LLM call logic."""
           # Your custom implementation
           return LLMResponse(
               content="Generated content",
               model=self.config.model,
               token_usage=TokenUsage(input_tokens=100, output_tokens=200)
           )
       
       def get_available_models(self) -> List[str]:
           """Return available models."""
           return ["custom-model-1", "custom-model-2"]

   # Register custom provider
   from arxiv_writer.llm import register_provider
   register_provider("custom", CustomProvider)

Provider Fallback Chain
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from arxiv_writer.llm import EnhancedLLMCaller

   config = {
       "providers": [
           {
               "provider": "openai",
               "model": "gpt-4",
               "priority": 1,
               "api_key": "sk-..."
           },
           {
               "provider": "anthropic", 
               "model": "claude-3-sonnet",
               "priority": 2,
               "api_key": "sk-ant-..."
           },
           {
               "provider": "google",
               "model": "gemini-pro",
               "priority": 3,
               "api_key": "AIza..."
           }
       ],
       "fallback_strategy": "priority_order",
       "max_fallback_attempts": 2
   }

   caller = EnhancedLLMCaller(config)
   
   # Will try OpenAI first, then Anthropic, then Google
   response = caller.call_llm_with_fallback(messages)
   print(f"Used provider: {response.provider}")

This LLM integration layer provides a robust, extensible foundation for working with multiple language model providers while maintaining a consistent interface throughout the ArXiv Writer system.