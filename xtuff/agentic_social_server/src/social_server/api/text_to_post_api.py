"""
Text-to-Post API for Social Xtuff

Accepts text submissions to AI personas and generates social media posts.
Auto-detects URLs and passes them through unmodified.
"""

import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import logging
import sys
from pathlib import Path

# Add the project root to Python path for proper imports
project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from social_server.modules.ai_personas import AIPersonaManager
from social_server.modules.generate_social_feed import SocialFeedManager, SocialFeedGenerator
from social_server.modules.generate_social_feed.social_models import SocialPost, PostType
from social_server.modules.generate_social_feed.feed_generator import FeedGenerator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("text_to_post_api")

app = FastAPI(
    title="Social Xtuff Text-to-Post API",
    description="Submit text to AI personas and generate optimized social media posts",
    version="1.0.0"
)

# CORS middleware for web requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class TextSubmissionRequest(BaseModel):
    text: str = Field(..., description="Text content to transform into a post")
    persona_id: str = Field(..., description="ID of the AI persona to use")
    user_id: Optional[str] = Field(default="anonymous", description="User submitting the request")
    model_override: Optional[str] = Field(default=None, description="Override the persona's default model")
    preserve_urls: bool = Field(default=True, description="Auto-detect and preserve URLs in the text")

class PostGenerationResponse(BaseModel):
    success: bool
    post_id: Optional[str] = None
    content: Optional[str] = None
    detected_urls: List[str] = []
    persona_name: str = ""
    generated_by_model: str = ""
    timestamp: str = ""
    error_message: Optional[str] = None

class AvailablePersonasResponse(BaseModel):
    personas: List[Dict[str, Any]]

# Global managers (initialized on startup)
persona_manager: Optional[AIPersonaManager] = None
feed_manager: Optional[SocialFeedManager] = None
feed_generator: Optional[FeedGenerator] = None

@app.on_event("startup")
async def startup_event():
    """Initialize managers on startup."""
    global persona_manager, feed_manager, feed_generator

    logger.info("Starting Text-to-Post API...")

    try:
        persona_manager = AIPersonaManager()
        feed_manager = SocialFeedManager()
        feed_generator = FeedGenerator()
        logger.info("Managers initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize managers: {e}")
        raise

def detect_urls(text: str) -> List[str]:
    """Detect URLs in text using regex."""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text)
    return urls

def create_url_preserved_prompt(text: str, urls: List[str]) -> str:
    """Create a prompt that instructs the AI to preserve URLs."""
    if not urls:
        return text

    url_list = "\n".join([f"- {url}" for url in urls])
    prompt = f"""Please transform the following text into an engaging social media post while preserving these URLs exactly as they appear:

URLs to preserve:
{url_list}

Original text:
{text}

IMPORTANT: Include the URLs in your response exactly as listed above, without modification."""

    return prompt

@app.get("/", response_model=Dict[str, str])
async def root():
    """API health check."""
    return {
        "message": "Social Xtuff Text-to-Post API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/personas", response_model=AvailablePersonasResponse)
async def get_available_personas():
    """Get list of available AI personas."""
    if not persona_manager:
        raise HTTPException(status_code=500, detail="Persona manager not initialized")

    personas = persona_manager.get_all_personas()

    persona_list = []
    for persona in personas:
        persona_list.append({
            "persona_id": persona.persona_id,
            "name": persona.name,
            "handle": persona.handle,
            "bio": persona.bio,
            "specialty": persona.specialty,
            "avatar_emoji": persona.avatar_emoji,
            "neurochemical_benefit": getattr(persona, 'neurochemical_benefit', '')
        })

    return AvailablePersonasResponse(personas=persona_list)

@app.post("/submit", response_model=PostGenerationResponse)
async def submit_text_to_persona(
    request: TextSubmissionRequest,
    background_tasks: BackgroundTasks
):
    """Submit text to a persona and generate a social media post."""

    if not all([persona_manager, feed_manager, feed_generator]):
        raise HTTPException(status_code=500, detail="Managers not initialized")

    logger.info(f"Processing text submission for persona {request.persona_id}")

    try:
        # Get the specified persona
        persona = persona_manager.get_persona(request.persona_id)
        if not persona:
            raise HTTPException(
                status_code=404,
                detail=f"Persona '{request.persona_id}' not found"
            )

        # Detect URLs if requested
        detected_urls = []
        processed_text = request.text

        if request.preserve_urls:
            detected_urls = detect_urls(request.text)
            if detected_urls:
                processed_text = create_url_preserved_prompt(request.text, detected_urls)
                logger.info(f"Detected {len(detected_urls)} URLs: {detected_urls}")

        # Create a custom prompt for the user-submitted text
        custom_prompt = f"""You are {persona.name}, {persona.bio}

Transform the following user-submitted text into an engaging social media post that reflects your personality and expertise:

"{processed_text}"

Requirements:
1. Maintain your unique voice and perspective as {persona.name}
2. Keep the core message and any URLs intact
3. Make it engaging and optimized for social media
4. Add relevant hashtags that fit your specialty: {persona.specialty}
5. Apply your four-factor neurochemical optimization (social connection, breakthrough insights, learning, mood elevation)

Respond with a JSON object containing:
{{
    "content": "your transformed post content",
    "engagement_hooks": ["hook1", "hook2"],
    "breakthrough_triggers": ["trigger1", "trigger2"],
    "learning_nuggets": ["nugget1", "nugget2"],
    "hashtags": ["tag1", "tag2", "tag3"],
    "learning_score": 0.7,
    "engagement_score": 0.8,
    "breakthrough_potential": 0.6,
    "mood_elevation_score": 0.7
}}"""

        # Generate post using the feed generator
        from social_server.modules.generate_social_feed.feed_generator import FeedGenerator

        # Create generator with model override if specified
        generator = FeedGenerator(model_override=request.model_override)

        # Use the generator's internal methods to create a single post
        post_type = PostType.BOOK_RECOMMENDATION  # Default type for user submissions

        # Override the generator's prompt creation for this custom request
        original_create_prompt = generator._create_content_prompt
        generator._create_content_prompt = lambda p, pt: custom_prompt

        try:
            # Generate a single post for this persona
            posts = generator._generate_persona_posts(persona, 1)

            if not posts:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to generate post from submitted text"
                )

            post = posts[0]

            # Add the post to the feed manager
            feed_manager.add_post(post)

            # Prepare response
            response = PostGenerationResponse(
                success=True,
                post_id=post.post_id,
                content=post.content,
                detected_urls=detected_urls,
                persona_name=persona.name,
                generated_by_model=getattr(post, 'generated_by_model', 'unknown'),
                timestamp=post.timestamp
            )

            logger.info(f"Successfully generated post {post.post_id} for {persona.name}")
            return response

        finally:
            # Restore original prompt method
            generator._create_content_prompt = original_create_prompt

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing text submission: {e}")
        return PostGenerationResponse(
            success=False,
            error_message=str(e),
            persona_name=persona.name if 'persona' in locals() else "unknown"
        )

@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    health_status = {
        "api_status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "managers": {
            "persona_manager": persona_manager is not None,
            "feed_manager": feed_manager is not None,
            "feed_generator": feed_generator is not None
        }
    }

    if persona_manager:
        try:
            personas = persona_manager.get_all_personas()
            health_status["persona_count"] = len(personas)
        except Exception as e:
            health_status["persona_manager_error"] = str(e)

    return health_status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=59312)