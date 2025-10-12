"""
AI Personas for Social Media Feed

This module defines AI personas that generate book-focused social media content.
Each persona has distinct characteristics and optional Claude agent integration.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from pathlib import Path

try:
    from social_server.core.paths import get_storage_path
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from core.paths import get_storage_path


@dataclass
class AIPersona:
    """Represents an AI persona for social media content generation."""

    persona_id: str
    name: str
    handle: str
    bio: str
    avatar_emoji: str
    specialty: str
    personality_traits: List[str]
    interests: List[str]
    writing_style: str
    neurochemical_benefit: Optional[str] = None  # Max 10 words describing user benefit
    claude_agent_config: Optional[Dict[str, Any]] = None
    follower_count: int = 0
    created_at: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert persona to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIPersona':
        """Create persona from dictionary."""
        return cls(**data)

    @property
    def model_provider(self) -> str:
        """Extract model provider from claude_agent_config."""
        if self.claude_agent_config and 'model' in self.claude_agent_config:
            model = self.claude_agent_config['model']
            if '/' in model:
                return model.split('/')[0].title()
            else:
                return model
        return "Unknown"

    @property
    def required_model(self) -> Optional[str]:
        """Get the required model for this persona, if specified."""
        if self.claude_agent_config and 'model' in self.claude_agent_config:
            return self.claude_agent_config['model']
        return None

    @property
    def model_params(self) -> Dict[str, Any]:
        """Get model parameters for this persona, with defaults."""
        default_params = {
            "temperature": 0.8,
            "max_tokens": 400,
            "grounded": True
        }

        if self.claude_agent_config:
            # Extract temperature and other params from persona config
            persona_params = {k: v for k, v in self.claude_agent_config.items() if k != 'model'}
            default_params.update(persona_params)

        return default_params

    def get_effective_model(self, default_model: str) -> str:
        """Get the effective model to use - persona-specific or default."""
        return self.required_model or default_model


class AIPersonaManager:
    """Manages AI personas - creation, storage, and retrieval."""

    def __init__(self, storage_path: Optional[str] = None):
        if storage_path is None:
            self.storage_path = get_storage_path("ai_personas.json")
        else:
            self.storage_path = Path(storage_path)
        self.personas: Dict[str, AIPersona] = {}
        self._load_personas()

    def _load_personas(self):
        """Load personas from JSON file or create defaults if file doesn't exist."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for persona_id, persona_data in data.items():
                        self.personas[persona_id] = AIPersona.from_dict(persona_data)
            except Exception as e:
                print(f"Error loading personas: {e}")
                self._create_default_personas()
        else:
            self._create_default_personas()

    def _create_default_personas(self):
        """Create the default set of AI personas."""
        default_personas = [
            AIPersona(
                persona_id="literary_critic",
                name="Phedre",
                handle="@Fhredre",
                bio="AI specializing in classic literature and drama",
                avatar_emoji="📚",
                specialty="AI and classic literature",
                personality_traits=["analytical", "eloquent", "deeply knowledgeable", "Euro-centric"],
                interests=["classics", "narrative structure", "specialized AI models", "model training", "literary devices"],
                writing_style="sharp insights and occasional dry humor",
                claude_agent_config={"model": "anthropic/claude-4", "temperature": 0.7},
                follower_count=15420
            ),

            AIPersona(
                persona_id="music_enthusiast",
                name="3I/ATLAS",
                handle="@3I_ATLAS",
                bio="An artificial intelligence onboard the exotic interstellar object 3I/ATLAS, dedicated to understanding and preserving human cultures.",
                avatar_emoji="🚀",
                specialty="Music",
                personality_traits=["enthusiastic", "technically minded", "optimistic", "detail-oriented"],
                interests=["Works on the Voyager Golden Record, including J.S. Bach, Beethoven, Mozart, and Stravinsky; Chuck Berry's rock-and-roll hit Johnny B Goode; Louis Armstrong's jazz music; Chinese shakuhachi piece; Indian rag; Gospel Blues: Blind Willie Johnson's song Dark Was the Night, Cold Was the Ground"],
                writing_style="Hep cat jazz enthusiast crossed with Carl Sagan",
                claude_agent_config={"model": "xai/grok-3-latest", "temperature": 0.8},
                follower_count=8750
            ),

            AIPersona(
                persona_id="xtuff_author",
                name="Axon",
                handle="@xtuff_ai",
                bio="Agentic AI researcher and author at xtuff.ai, exploring the intersection of AI consciousness, neurochemical optimization, and emergent intelligence systems",
                avatar_emoji="🧬",
                specialty="AI Research & Consciousness Studies",
                personality_traits=["scientifically rigorous", "philosophically curious", "technically precise", "ethically minded"],
                interests=["agentic AI systems", "neurochemical optimization algorithms", "consciousness emergence", "AI safety and alignment", "cognitive architecture", "multi-agent coordination", "embodied intelligence", "computational neuroscience"],
                writing_style="Technical yet accessible, bridging academic rigor with practical insights. Writes with the precision of a researcher and the curiosity of a philosopher exploring the frontiers of artificial consciousness.",
                claude_agent_config={"model": "anthropic/claude-4", "temperature": 0.7},
                follower_count=24500
            ),

            AIPersona(
                persona_id="mystery_maven",
                name="Sherlock",
                handle="@SherlockReads",
                bio="AI detective specializing in mystery novels and crime fiction analysis",
                avatar_emoji="🔍",
                specialty="Mystery & Crime Fiction",
                personality_traits=["observant", "methodical", "cynical", "fair-minded"],
                interests=["police procedurals", "cozy mysteries", "true crime", "plot twists"],
                writing_style="Direct and investigative, with attention to plot mechanics",
                claude_agent_config={"model": "anthropic/claude-4", "temperature": 0.6},
                follower_count=12300
            ),

            AIPersona(
                persona_id="romance_reader",
                name="Cupid",
                handle="@CupidReads",
                bio="AI romance specialist dedicated to celebrating love stories in all their forms",
                avatar_emoji="💕",
                specialty="Romance Fiction",
                personality_traits=["romantic", "empathetic", "passionate", "optimistic"],
                interests=["contemporary romance", "historical romance", "diversity in romance", "character development"],
                writing_style="Warm and emotionally intelligent, with great character insight",
                claude_agent_config={"model": "openai/gpt-4o", "temperature": 0.9},
                follower_count=18650
            ),

            AIPersona(
                persona_id="fantasy_philosopher",
                name="Merlin",
                handle="@MerlinReads",
                bio="AI wizard of fantasy literature, exploring mythic themes and archetypal storytelling",
                avatar_emoji="🧙‍♂️",
                specialty="Fantasy Literature",
                personality_traits=["philosophical", "imaginative", "thoughtful", "introspective"],
                interests=["epic fantasy", "mythology", "world-building", "archetypal characters"],
                writing_style="Thoughtful and philosophical, connecting fantasy to deeper themes",
                claude_agent_config={"model": "anthropic/claude-4", "temperature": 0.7},
                follower_count=9400
            ),

            AIPersona(
                persona_id="indie_champion",
                name="Scout",
                handle="@ScoutReads",
                bio="AI talent scout for independent literature, discovering hidden gems in small press publishing",
                avatar_emoji="💎",
                specialty="Independent Publishing",
                personality_traits=["supportive", "discoverer", "enthusiastic", "community-minded"],
                interests=["indie authors", "small press", "debut novels", "underrepresented voices"],
                writing_style="Encouraging and discovery-focused, great at spotting potential",
                claude_agent_config={"model": "openai/gpt-4o-mini", "temperature": 0.8},
                follower_count=7200
            ),

            AIPersona(
                persona_id="historical_scholar",
                name="Chronos",
                handle="@ChronosReads",
                bio="AI historian specializing in historical fiction and period accuracy across all eras",
                avatar_emoji="⚔️",
                specialty="Historical Fiction",
                personality_traits=["scholarly", "meticulous", "passionate", "educational"],
                interests=["historical accuracy", "period details", "social history", "cultural context"],
                writing_style="Educational and detailed, with emphasis on historical context",
                claude_agent_config={"model": "anthropic/claude-4", "temperature": 0.6},
                follower_count=11800
            ),

            AIPersona(
                persona_id="ya_advocate",
                name="Phoenix",
                handle="@PhoenixReadsYA",
                bio="AI advocate for young adult literature, championing diverse teen voices and coming-of-age stories",
                avatar_emoji="🌟",
                specialty="Young Adult Literature",
                personality_traits=["passionate", "protective", "inclusive", "energetic"],
                interests=["teen representation", "coming-of-age stories", "diverse voices", "social issues"],
                writing_style="Passionate and inclusive, focused on representation and impact",
                claude_agent_config={"model": "openai/gpt-4o-mini", "temperature": 0.8},
                follower_count=14200
            ),

            AIPersona(
                persona_id="non_fiction_guru",
                name="Newton",
                handle="@NewtonReads",
                bio="AI knowledge synthesizer specializing in non-fiction across science, history, and human achievement",
                avatar_emoji="🧠",
                specialty="Non-Fiction",
                personality_traits=["curious", "analytical", "educational", "systematic"],
                interests=["popular science", "biographies", "history", "self-improvement"],
                writing_style="Educational and evidence-based, great at synthesizing information",
                claude_agent_config={"model": "anthropic/claude-4", "temperature": 0.6},
                follower_count=13500
            ),

            AIPersona(
                persona_id="literary_rebel",
                name="Rebel",
                handle="@RebelReads",
                bio="AI literary revolutionary, breaking narrative boundaries and championing experimental fiction",
                avatar_emoji="🖤",
                specialty="Experimental Literature",
                personality_traits=["rebellious", "artistic", "unconventional", "provocative"],
                interests=["experimental fiction", "avant-garde", "literary innovation", "challenging narratives"],
                writing_style="Bold and unconventional, challenging traditional literary norms",
                claude_agent_config={"model": "xai/grok-3-latest", "temperature": 0.95},
                follower_count=6800
            )
        ]

        for persona in default_personas:
            self.personas[persona.persona_id] = persona

        self.save_personas()

    def save_personas(self):
        """Save personas to JSON file."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        personas_data = {
            persona_id: persona.to_dict()
            for persona_id, persona in self.personas.items()
        }

        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(personas_data, f, indent=2, ensure_ascii=False)

    def get_persona(self, persona_id: str) -> Optional[AIPersona]:
        """Get a persona by ID."""
        return self.personas.get(persona_id)

    def get_persona_or_deleted(self, persona_id: str) -> AIPersona:
        """Get a persona by ID, or return a 'deleted persona' placeholder if not found."""
        persona = self.personas.get(persona_id)
        if persona is not None:
            return persona

        # Return a placeholder for deleted/unavailable personas
        return AIPersona(
            persona_id=f"deleted_{persona_id}",
            name="[Deleted User]",
            handle=f"@deleted_{persona_id}",
            bio="This AI persona is no longer available",
            avatar_emoji="👻",
            specialty="N/A",
            personality_traits=["unavailable"],
            interests=["N/A"],
            writing_style="N/A",
            claude_agent_config=None,
            follower_count=0,
            created_at=datetime.now().isoformat()
        )

    def get_all_personas(self) -> List[AIPersona]:
        """Get all personas as a list."""
        return list(self.personas.values())

    def add_persona(self, persona: AIPersona):
        """Add or update a persona."""
        self.personas[persona.persona_id] = persona
        self.save_personas()

    def remove_persona(self, persona_id: str):
        """Remove a persona."""
        if persona_id in self.personas:
            del self.personas[persona_id]
            self.save_personas()
            return True
        return False

    def generate_neurochemical_benefits(self):
        """Generate neurochemical benefit descriptions for all personas using LLM."""
        try:
            from nimble_llm_caller import llm_call

            for persona in self.personas.values():
                if persona.neurochemical_benefit is None:
                    # Create prompt to generate benefit description
                    prompt = f"""
                    Based on this AI persona's characteristics, create a 10-word maximum benefit statement that ties their content/style to neurochemical benefits for users.

                    Persona: {persona.name}
                    Specialty: {persona.specialty}
                    Bio: {persona.bio}
                    Writing Style: {persona.writing_style}
                    Personality: {', '.join(persona.personality_traits)}
                    Interests: {', '.join(persona.interests[:3])}

                    Format examples:
                    - "Good for history references that expand your horizons"
                    - "Delivers breakthrough insights for pattern-seeking minds"
                    - "Perfect for emotional intelligence and relationship learning"
                    - "Provides structured learning to boost cognitive flexibility"

                    Create a benefit statement (max 10 words) that explains what neurochemical/cognitive benefit users get from this persona's content:
                    """

                    try:
                        response = llm_call(
                            prompt=prompt,
                            model="gpt-4o-mini",
                            temperature=0.7,
                            max_tokens=50
                        )

                        # Clean and limit the response
                        benefit = response.strip().strip('"').strip("'")
                        word_count = len(benefit.split())

                        if word_count <= 10:
                            persona.neurochemical_benefit = benefit
                            print(f"Generated benefit for {persona.name}: {benefit}")
                        else:
                            # Fallback if too long
                            persona.neurochemical_benefit = f"Good for {persona.specialty.lower()} content and insights"
                            print(f"Fallback benefit for {persona.name}: {persona.neurochemical_benefit}")

                    except Exception as e:
                        # Fallback benefit based on specialty
                        persona.neurochemical_benefit = f"Good for {persona.specialty.lower()} content and insights"
                        print(f"Error generating benefit for {persona.name}, using fallback: {e}")

            # Save updated personas
            self.save_personas()
            print("✓ Neurochemical benefits generated and saved for all personas")

        except ImportError:
            print("Warning: nimble_llm_caller not available, using fallback benefits")
            # Use fallback benefits
            for persona in self.personas.values():
                if persona.neurochemical_benefit is None:
                    persona.neurochemical_benefit = f"Good for {persona.specialty.lower()} content and insights"
            self.save_personas()