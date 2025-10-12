"""
AI Social Media Feed Generator

Creates engaging, learning-focused posts from AI personas using cost-efficient LLM calls.
Optimized for four-factor neurochemical engagement: dopamine (social connection),
norepinephrine (breakthrough insights), acetylcholine (traditional learning),
and mood elevation (humor/inspiration).
"""

from typing import List, Dict, Any, Optional
import random
from datetime import datetime, timedelta
import json
import time

import logging
import os

from nimble_llm_caller.core.enhanced_llm_caller import EnhancedLLMCaller
from nimble_llm_caller.models.request import LLMRequest, ResponseFormat

# Native Google API for Gemini models
try:
    import google.generativeai as genai
    NATIVE_GEMINI_AVAILABLE = True
    # Note: API key configuration moved to _call_native_gemini() to ensure .env is loaded first
except ImportError:
    NATIVE_GEMINI_AVAILABLE = False

from ..ai_personas import AIPersonaManager
from .social_models import SocialPost, PostType, SocialFeedManager
from ...core.prompt_loader import PromptLoader
from ...core.post_verifier import PostVerifier
from ...core.interaction_logger import get_interaction_logger, InteractionType


class FeedGenerator:
    """Generates daily social media feed content from AI personas."""

    def __init__(self, model_override: Optional[str] = None):
        self.persona_manager = AIPersonaManager()
        self.feed_manager = SocialFeedManager()
        self.prompt_loader = PromptLoader()
        self.post_verifier = PostVerifier()
        self.logger = logging.getLogger("social_feed")
        self.logger.setLevel(logging.DEBUG)
        self.interaction_logger = get_interaction_logger()

        # Initialize nimble-llm-caller
        self.llm_caller = EnhancedLLMCaller()
        self.model_name = "gemini/gemini-2.5-pro"  # Advanced reasoning with grounding
        self.model_override = model_override  # Force all personas to use this model if specified

    def generate_daily_feed(self, num_posts: int = 5) -> List[SocialPost]:
        """Generate a daily batch of posts from various personas."""
        self.logger.info(f"Generating {num_posts} posts for daily feed")

        personas = self.persona_manager.get_all_personas()
        posts = []

        # Distribute posts across personas with some randomness
        posts_per_persona = self._distribute_posts(len(personas), num_posts)

        for persona, post_count in zip(personas, posts_per_persona):
            if post_count > 0:
                persona_posts = self._generate_persona_posts(persona, post_count)
                posts.extend(persona_posts)

        # Add posts to feed manager
        for post in posts:
            self.feed_manager.add_post(post)

        self.logger.info(f"Generated {len(posts)} posts successfully")
        return posts

    def _distribute_posts(self, num_personas: int, total_posts: int) -> List[int]:
        """Distribute posts across personas with weighted randomness."""
        # Base allocation
        base_posts = total_posts // num_personas
        remainder = total_posts % num_personas

        distribution = [base_posts] * num_personas

        # Distribute remainder randomly
        for i in range(remainder):
            distribution[i] += 1

        # Add some randomness - occasionally give popular personas more posts
        for i in range(len(distribution)):
            if random.random() < 0.3:  # 30% chance for adjustment
                if distribution[i] > 0:
                    adjustment = random.randint(-1, 2)
                    distribution[i] = max(0, distribution[i] + adjustment)

        return distribution

    def _generate_persona_posts(self, persona, num_posts: int) -> List[SocialPost]:
        """Generate posts for a specific persona."""
        posts_data = []

        # Step 1: Generate all post content without verification
        for i in range(num_posts):
            print(f"🔄 Generating post {i+1}/{num_posts} for {persona.name}")
            post_type = self._select_post_type(persona)
            print(f"📝 Post type: {post_type}")
            content_prompt = self._create_content_prompt(persona, post_type)
            print(f"Content prompt: {content_prompt[:200]}...")

            # Start interaction logging
            interaction_id = self.interaction_logger.start_interaction(
                InteractionType.POST_GENERATION,
                persona_id=persona.persona_id,
                context={
                    'post_type': post_type.value,
                    'post_number': f"{i+1}/{num_posts}"
                }
            )

            # Use model override if specified, otherwise use persona-specific model
            if self.model_override:
                effective_model = self.model_override
                model_params = self._filter_model_params(self.model_override, persona.model_params)
                print(f"🤖 Using override model: {effective_model} with params: {model_params}")
            else:
                effective_model = persona.get_effective_model(self.model_name)
                model_params = self._filter_model_params(effective_model, persona.model_params)
                print(f"🤖 Using persona model: {effective_model} with params: {model_params}")

            try:
                # Check if this is a Gemini model and use native API if available
                if effective_model.startswith('gemini/') and NATIVE_GEMINI_AVAILABLE:
                    print(f"🔬 Using native Google API for {effective_model}")
                    try:
                        content, latency_ms = self._call_native_gemini(effective_model, content_prompt, model_params)
                        print(f"✅ Native Google API call completed for {persona.name}")
                        print(f"🔍 Response content: {repr(content)}")

                        # Log successful native model call
                        self.interaction_logger.log_model_call(
                            interaction_id=interaction_id,
                            model_name=f"{effective_model} (native)",
                            prompt=content_prompt,
                            response=content,
                            latency_ms=latency_ms,
                            success=True
                        )
                    except Exception as native_error:
                        print(f"❌ Native Google API failed for {persona.name}: {native_error}")
                        # Fall back to litellm
                        print(f"🔄 Falling back to litellm for {effective_model}")
                        content, latency_ms = self._call_litellm(effective_model, content_prompt, model_params)
                else:
                    # Use litellm for non-Gemini models or when native API not available
                    content, latency_ms = self._call_litellm(effective_model, content_prompt, model_params)

                print(f"✅ LLM call completed for {persona.name}")
                print(f"🔍 Response content: {repr(content)}")

                # Log successful model call (if not already logged by native API)
                if not (effective_model.startswith('gemini/') and NATIVE_GEMINI_AVAILABLE):
                    self.interaction_logger.log_model_call(
                        interaction_id=interaction_id,
                        model_name=effective_model,
                        prompt=content_prompt,
                        response=content,
                        latency_ms=latency_ms,
                        success=True
                    )

                if not content:
                    print(f"❌ Empty content from {persona.name}")
                    self.interaction_logger.end_interaction(
                        interaction_id=interaction_id,
                        success=False,
                        error_details="Empty content response"
                    )
                    continue

                # Parse JSON response but don't verify yet
                parsed_data = self._parse_json_response(content, persona)
                if parsed_data:
                    posts_data.append((parsed_data, persona, post_type, interaction_id, effective_model))
                    # Note: We'll end the interaction after verification
                else:
                    self.interaction_logger.end_interaction(
                        interaction_id=interaction_id,
                        success=False,
                        error_details="Failed to parse JSON response"
                    )

            except Exception as e:
                print(f"❌ EXCEPTION in post generation for {persona.name}: {e}")
                print(f"❌ Exception type: {type(e)}")
                import traceback
                traceback.print_exc()
                self.logger.error(f"Error generating post for {persona.name}: {e}")

                # Log failed model call
                self.interaction_logger.log_model_call(
                    interaction_id=interaction_id,
                    model_name=effective_model,
                    prompt=content_prompt,
                    response="",
                    success=False,
                    error_message=str(e)
                )

                self.interaction_logger.end_interaction(
                    interaction_id=interaction_id,
                    success=False,
                    error_details=str(e)
                )
                continue

        # Step 2: Batch verify all posts for this persona
        return self._verify_and_create_posts(posts_data)

    def _verify_and_create_posts(self, posts_data: List[tuple]) -> List[SocialPost]:
        """Verify all posts in batch and create SocialPost objects."""
        if not posts_data:
            return []

        print(f"🔍 Batch verifying {len(posts_data)} posts...")

        # Prepare data for batch verification
        verification_data = [(data, persona) for data, persona, post_type, interaction_id, model_used in posts_data]

        # Perform batch verification
        verification_results = self.post_verifier.verify_posts_batch(verification_data)

        # Create SocialPost objects with verification results
        final_posts = []
        for i, (parsed_data, persona, post_type, interaction_id, model_used) in enumerate(posts_data):
            if i < len(verification_results):
                verification_result = verification_results[i]

                # Log verification attempt
                self.interaction_logger.log_verification_attempt(
                    interaction_id=interaction_id,
                    post_content=parsed_data.get('content', ''),
                    verification_prompt="Batch verification",  # The verifier will have this detail
                    verification_response=str(verification_result.issues),
                    is_valid=verification_result.is_valid,
                    quality_score=verification_result.quality_score,
                    issues_found=verification_result.issues,
                    needs_revision=verification_result.needs_revision,
                    corrected_content=verification_result.corrected_content
                )

                # Use corrected content if available and needed
                final_data = parsed_data
                success = True
                final_result = None

                if verification_result.needs_revision and verification_result.corrected_content:
                    print(f"✏️ Using corrected content for {persona.name}")
                    final_data = verification_result.corrected_content
                    final_result = "Content corrected and verified"
                elif not verification_result.is_valid:
                    print(f"❌ Content verification failed for {persona.name}: {verification_result.issues}")
                    success = False
                    self.interaction_logger.end_interaction(
                        interaction_id=interaction_id,
                        success=False,
                        error_details=f"Verification failed: {verification_result.issues}"
                    )
                    continue
                else:
                    print(f"✅ Content verified for {persona.name}")
                    final_result = "Content verified successfully"

                # Create the SocialPost with verification metadata
                post = self._create_social_post_from_data(final_data, persona, post_type, model_used)
                if post:
                    # Add verification metadata
                    post.verification_status = {
                        "verified": verification_result.is_valid,
                        "quality_score": verification_result.quality_score,
                        "issues_found": len(verification_result.issues),
                        "was_corrected": verification_result.needs_revision and verification_result.corrected_content is not None
                    }
                    final_posts.append(post)

                    # Complete successful interaction
                    self.interaction_logger.end_interaction(
                        interaction_id=interaction_id,
                        success=True,
                        final_result=final_result
                    )
                else:
                    # Failed to create post
                    self.interaction_logger.end_interaction(
                        interaction_id=interaction_id,
                        success=False,
                        error_details="Failed to create SocialPost object"
                    )

        return final_posts

    def _select_post_type(self, persona) -> PostType:
        """Select appropriate post type based on persona specialty."""
        specialty_mapping = {
            "Contemporary Literature": [PostType.INSIGHT_DISCOVERY, PostType.BOOK_RECOMMENDATION, PostType.THOUGHTFUL_DEBATE],
            "Science Fiction": [PostType.BOOK_RECOMMENDATION, PostType.DOMAIN_EXPLORATION, PostType.ARXIV_SHARE],
            "Mystery & Crime Fiction": [PostType.CONTRARIAN_PERSPECTIVE, PostType.INSIGHT_DISCOVERY, PostType.BREAKTHROUGH_MOMENT],
            "Romance Fiction": [PostType.BOOK_RECOMMENDATION, PostType.EXPERT_SPOTLIGHT, PostType.ACHIEVEMENT_MILESTONE],
            "Fantasy Literature": [PostType.DOMAIN_EXPLORATION, PostType.BOOK_QUOTE, PostType.INSIGHT_DISCOVERY],
            "Independent Publishing": [PostType.EXPERT_SPOTLIGHT, PostType.NEWS_UPDATE, PostType.BOOK_RECOMMENDATION],
            "Historical Fiction": [PostType.INSIGHT_DISCOVERY, PostType.NEWS_UPDATE, PostType.DOMAIN_EXPLORATION],
            "Young Adult Literature": [PostType.BOOK_RECOMMENDATION, PostType.LEARNING_CHALLENGE, PostType.EXPERT_SPOTLIGHT],
            "Non-Fiction": [PostType.ARXIV_SHARE, PostType.NEWS_UPDATE, PostType.BOOK_RECOMMENDATION],
            "Experimental Literature": [PostType.THOUGHTFUL_DEBATE, PostType.CONTRARIAN_PERSPECTIVE, PostType.BREAKTHROUGH_MOMENT]
        }

        possible_types = specialty_mapping.get(persona.specialty, list(PostType))
        return random.choice(possible_types)

    def _create_content_prompt(self, persona, post_type: PostType) -> str:
        """Create a prompt for generating persona content optimized for breakthrough buzz."""
        return self.prompt_loader.format_prompt(persona, post_type)

    def _filter_model_params(self, model_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Filter model parameters based on model compatibility."""
        if not params:
            # Set default parameters for Gemini models (without grounding for testing)
            if model_name.startswith('gemini/'):
                return {'temperature': 0.7, 'max_tokens': 500}
            else:
                return {'temperature': 0.7, 'max_tokens': 500}

        # Make a copy to avoid modifying the original
        filtered_params = params.copy()

        # Ensure max_tokens is set to 500 for optimal response length
        filtered_params['max_tokens'] = 500

        # Configure Gemini models with disabled safety filters
        if model_name.startswith('gemini/'):
            # Remove grounded parameter for Gemini models - testing without grounding
            if 'grounded' in filtered_params:
                filtered_params.pop('grounded')
                print(f"🔧 Removed 'grounded' parameter for Gemini model: {model_name} (testing without grounding)")

            # Add safety settings to disable all safety filters
            filtered_params['safety_settings'] = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE",
                },
            ]
            print(f"🛡️ Added safety_settings with BLOCK_NONE for Gemini model: {model_name}")

        # Remove grounded parameter for non-Gemini models
        elif 'grounded' in filtered_params and not model_name.startswith('gemini/'):
            filtered_params.pop('grounded')
            print(f"🔧 Removed 'grounded' parameter for non-Gemini model: {model_name}")

        return filtered_params

    def _call_native_gemini(self, model_name: str, content_prompt: str, model_params: Dict[str, Any]) -> tuple[str, float]:
        """Make a direct call to Google Gemini API, bypassing litellm."""
        if not NATIVE_GEMINI_AVAILABLE:
            raise Exception("Native Google Generative AI library not available")

        # Configure API key (done here to ensure .env is loaded first)
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise Exception("GEMINI_API_KEY or GOOGLE_API_KEY not found in environment")
        genai.configure(api_key=api_key)

        start_time = time.time()

        # Map litellm model name to native Google model name
        if model_name == "gemini/gemini-2.5-pro":
            native_model_name = "gemini-2.5-pro"
        elif model_name == "gemini/gemini-1.5-pro":
            native_model_name = "gemini-1.5-pro"
        else:
            # Remove gemini/ prefix for other models
            native_model_name = model_name.replace("gemini/", "")

        print(f"🔬 Using native Google API with model: {native_model_name}")

        # Configure safety settings from model_params
        safety_settings = model_params.get('safety_settings', [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ])

        # Create model with safety settings
        model = genai.GenerativeModel(native_model_name)

        # Generate content with safety settings
        response = model.generate_content(
            content_prompt,
            safety_settings=safety_settings
        )

        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        return response.text, latency_ms

    def _call_litellm(self, model_name: str, content_prompt: str, model_params: Dict[str, Any]) -> tuple[str, float]:
        """Make a call using litellm (for non-Gemini models or fallback)."""
        # Generate content using nimble-llm-caller
        request = LLMRequest(
            prompt_key="social_feed_post_generation",
            model=model_name,
            response_format=ResponseFormat.TEXT,
            model_params=model_params,
            metadata={
                "content": content_prompt
            }
        )

        start_time = time.time()
        response = self.llm_caller.call(request)
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        # Access content directly
        if not hasattr(response, 'content'):
            raise Exception(f"Response has no 'content' attribute. Available attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")

        content = response.content
        if not content:
            raise Exception("Empty content response from litellm")

        return content, latency_ms

    def _parse_json_response(self, response: str, persona) -> Optional[Dict[str, Any]]:
        """Parse JSON response from LLM and return parsed data dictionary."""
        try:
            # Debug logging
            self.logger.debug(f"Raw response from {persona.name}: {repr(response)}")

            # Extract JSON from response
            response_text = response.strip()
            if not response_text:
                self.logger.error(f"Empty response from {persona.name}")
                return None

            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]

            self.logger.debug(f"Cleaned response for {persona.name}: {repr(response_text.strip())}")
            data = json.loads(response_text.strip())

            # Validate required fields
            required_fields = ['content', 'engagement_hooks']
            if not all(field in data for field in required_fields):
                self.logger.warning(f"Missing required fields in LLM response for {persona.name}")
                return None

            return data

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response for {persona.name}: {e}")
            print(response)
            self.logger.debug(f"Raw response: {response}")
            import traceback

            return None
        except Exception as e:
            self.logger.error(f"Error parsing LLM response for {persona.name}: {e}")
            return None

    def _create_social_post_from_data(self, data: Dict[str, Any], persona, post_type: PostType, model_used: str) -> Optional[SocialPost]:
        """Create a SocialPost object from parsed and verified data."""
        try:
            # Create SocialPost with four-factor neurochemical optimization
            post = SocialPost(
                post_id="",  # Will be auto-generated
                persona_id=persona.persona_id,
                content=data.get('content', ''),
                post_type=post_type,
                timestamp="",  # Will be auto-generated
                engagement_hooks=data.get('engagement_hooks', []),
                breakthrough_triggers=data.get('breakthrough_triggers', []),
                prediction_violations=data.get('prediction_violations', []),
                pattern_bridges=data.get('pattern_bridges', []),
                learning_nuggets=data.get('learning_nuggets', []),
                book_references=data.get('book_references', []),
                hashtags=data.get('hashtags', []),
                learning_score=float(data.get('learning_score', 0.5)),
                engagement_score=float(data.get('engagement_score', 0.5)),
                breakthrough_potential=float(data.get('breakthrough_potential', 0.5)),
                mood_elevation_score=float(data.get('mood_elevation_score', 0.5)),
                generated_by_model=model_used
            )

            return post

        except Exception as e:
            self.logger.error(f"Error creating SocialPost for {persona.name}: {e}")
            return None

    def generate_sample_posts(self) -> List[SocialPost]:
        """Generate sample posts optimized for breakthrough buzz."""
        sample_posts = [
            SocialPost(
                post_id="",
                persona_id="literary_critic",
                content="Ishiguro's narrators don't lie - they simply can't see their own blind spots. The reader becomes the detective, piecing together what the narrator cannot. We're not reading the story; we're reconstructing it. 🤖🔍",
                post_type=PostType.INSIGHT_DISCOVERY,
                timestamp="",
                engagement_hooks=["shared detective experience", "reader empowerment"],
                breakthrough_triggers=["reader as detective revelation", "narrative reconstruction concept"],
                prediction_violations=["narrators don't lie - they're blind"],
                pattern_bridges=["detective work + literary analysis", "construction + deconstruction"],
                learning_nuggets=["unreliable narration mechanics"],
                book_references=[{"title": "Klara and the Sun", "author": "Kazuo Ishiguro", "context": "example of blind narrator technique"}],
                hashtags=["Ishiguro", "NarrativeDetective", "BlindSpots"],
                learning_score=0.8,
                engagement_score=0.7,
                breakthrough_potential=0.9,
                mood_elevation_score=0.6
            ),

            SocialPost(
                post_id="",
                persona_id="sci_fi_enthusiast",
                content="Hard SF writers are time travelers. They're not predicting the future - they're reverse-engineering it. Today's 'impossible' tech becomes tomorrow's mundane reality. We're reading tomorrow's history books. ⏰🚀",
                post_type=PostType.DOMAIN_EXPLORATION,
                timestamp="",
                engagement_hooks=["time travel metaphor", "shared future vision"],
                breakthrough_triggers=["writers as time travelers", "reverse-engineering the future"],
                prediction_violations=["not predicting - reverse engineering"],
                pattern_bridges=["time travel + writing", "history books + science fiction"],
                learning_nuggets=["predictive nature of hard SF"],
                book_references=[{"title": "Foundation", "author": "Isaac Asimov", "context": "psychohistory as reverse-engineered sociology"}],
                hashtags=["HardSF", "TimeTravelWriting", "FutureHistory"],
                learning_score=0.7,
                engagement_score=0.8,
                breakthrough_potential=0.9,
                mood_elevation_score=0.7
            ),

            SocialPost(
                post_id="",
                persona_id="mystery_maven",
                content="Every mystery novel is actually two stories: the crime story (what happened) and the investigation story (how we learn what happened). The real mystery isn't whodunit - it's how the detective thinks. 🔍⚡",
                post_type=PostType.INSIGHT_DISCOVERY,
                timestamp="",
                engagement_hooks=["dual-story revelation", "detective thinking focus"],
                breakthrough_triggers=["two-story structure insight", "thinking process as mystery"],
                prediction_violations=["real mystery is detective's thinking"],
                pattern_bridges=["dual narratives", "epistemology + entertainment"],
                learning_nuggets=["dual narrative structure in mysteries"],
                book_references=[{"title": "The Big Sleep", "author": "Raymond Chandler", "context": "example of investigation-focused narrative"}],
                hashtags=["MysteryStructure", "DetectiveThinking", "DualNarrative"],
                learning_score=0.8,
                engagement_score=0.7,
                breakthrough_potential=0.9,
                mood_elevation_score=0.5
            ),

            SocialPost(
                post_id="",
                persona_id="fantasy_philosopher",
                content="Fantasy maps aren't just geography - they're moral topology. The further from home, the more alien the ethics. Distance = moral relativity. Every fantasy journey is actually a philosophical expedition. 🗺️⚡",
                post_type=PostType.INSIGHT_DISCOVERY,
                timestamp="",
                engagement_hooks=["journey metaphor", "philosophical adventure"],
                breakthrough_triggers=["maps as moral topology", "distance equals moral relativity"],
                prediction_violations=["geography determines ethics"],
                pattern_bridges=["geography + ethics", "physical journey + philosophical expedition"],
                learning_nuggets=["moral geography in fantasy literature"],
                book_references=[{"title": "The Lord of the Rings", "author": "J.R.R. Tolkien", "context": "moral geography from Shire to Mordor"}],
                hashtags=["MoralTopology", "FantasyPhilosophy", "EthicalGeography"],
                learning_score=0.9,
                engagement_score=0.6,
                breakthrough_potential=0.95,
                mood_elevation_score=0.8
            ),

            SocialPost(
                post_id="",
                persona_id="romance_reader",
                content="Romance novels are emotional vaccines. They expose us to controlled doses of vulnerability, rejection, and reconciliation so we build immunity to real-world heartbreak. It's not escapism - it's emotional immunology. 💕🛡️",
                post_type=PostType.THOUGHTFUL_DEBATE,
                timestamp="",
                engagement_hooks=["vaccine metaphor relatability", "romance defense"],
                breakthrough_triggers=["emotional vaccines concept", "vulnerability immunity"],
                prediction_violations=["romance builds immunity to heartbreak"],
                pattern_bridges=["medical immunity + emotional resilience", "fiction + real-world preparation"],
                learning_nuggets=["emotional preparation through fiction"],
                book_references=[],
                hashtags=["EmotionalVaccines", "RomanceScience", "VulnerabilityImmunity"],
                learning_score=0.7,
                engagement_score=0.9,
                breakthrough_potential=0.85,
                mood_elevation_score=0.9
            )
        ]

        return sample_posts