"""
Services for GPT integration and mock responses.

Direct GPT-4 hypothesis generation (Agent-Tron/LPM/Data Engine unhooked for now).
"""
import os
import json
import random
import logging
from typing import Dict, List, Optional
from .sim_models import PersonaAgent

logger = logging.getLogger(__name__)

# Agent-Tron/LPM/Data Engine are unhooked - using direct GPT-4

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from decouple import config
    # Try to load from .env file
    OPENAI_API_KEY = config('OPENAI_API_KEY', default=None) or config('OPENAI_KEY', default=None)
except ImportError:
    # Fallback to environment variables if decouple not available
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') or os.environ.get('OPENAI_KEY')

# Initialize OpenAI client if API key is available
client = None
print(f"[DEBUG] OPENAI_AVAILABLE: {OPENAI_AVAILABLE}")
print(f"[DEBUG] OPENAI_API_KEY present: {OPENAI_API_KEY is not None}")
print(f"[DEBUG] OPENAI_API_KEY length: {len(OPENAI_API_KEY) if OPENAI_API_KEY else 0}")

if OPENAI_AVAILABLE and OPENAI_API_KEY:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        print(f"✓ OpenAI client initialized successfully (GPT-4o ready for agent chat)")
    except Exception as e:
        print(f"✗ Failed to initialize OpenAI client: {e}")
        import traceback
        traceback.print_exc()
        client = None
else:
    if not OPENAI_AVAILABLE:
        print("⚠ OpenAI package not installed. Install with: pip install openai")
    elif not OPENAI_API_KEY:
        print("⚠ OPENAI_API_KEY not set. Please set it in backend/.env file.")
        print("   Example: OPENAI_API_KEY=sk-your-key-here")
        print("   Then restart the Django server.")


def generate_persona_response(
    agent: PersonaAgent,
    task_type: str,
    payload: Dict,
    mode: str = 'gpt',  # Default to GPT
    agent_tron_context: Optional[Dict] = None  # Not used (Agent-Tron unhooked)
) -> Dict:
    """
    Generate a persona response using GPT or mock.
    
    Direct GPT-4 hypothesis generation (Agent-Tron/LPM/Data Engine unhooked).
    Enhanced prompts provide unique insights for beauty, food, and AITANA questions.
    
    Args:
        agent: PersonaAgent instance
        task_type: 'hypothesis', 'survey', 'taste_test', 'chat'
        payload: Task-specific payload
        mode: 'gpt' or 'mock'
        agent_tron_context: Not used (kept for compatibility)
    
    Returns:
        Dict with 'text' and optionally 'structured' data
    """
    print(f"[generate_persona_response] Mode: {mode}, Client available: {client is not None}, Task: {task_type}, Agent: {agent.display_name}")
    
    if mode == 'gpt':
        if not client:
            error_msg = 'GPT client not available. Please set OPENAI_API_KEY in backend/.env file.'
            print(f"ERROR: {error_msg}")
            return {
                'text': f"⚠️ {error_msg}",
                'structured': {}
            }
        print(f"[generate_persona_response] Calling GPT for {agent.display_name} (task: {task_type})")
        result = _generate_gpt_response(agent, task_type, payload, agent_tron_context=None)
        print(f"[generate_persona_response] GPT returned: {result.get('text', '')[:100]}...")
        return result
    else:
        # Only use mock if explicitly requested
        print(f"WARNING: Mock mode explicitly requested for {agent.display_name} - using mock")
        return _generate_mock_response(agent, task_type, payload)


def _build_default_system_prompt(agent: PersonaAgent) -> str:
    """Build a default system prompt if agent doesn't have one."""
    archetype_descriptions = {
        'value_seeker': 'You prioritize getting the best value and deals. Price is your main concern, and you always look for promotions, discounts, and combo meals. You compare prices across brands and are willing to switch if you find a better deal.',
        'health_optimizer': 'You focus on nutrition and healthy options. Ingredients, nutritional value, and freshness matter most to you. You read nutrition labels and prefer options with whole ingredients, lower calories, and better macro balance.',
        'convenience_loyalist': 'You value speed, reliability, and consistency. You stick with brands you know work well and can deliver quickly. Convenience and predictability are more important than trying new things.',
        'late_night_craver': 'You often order food late at night or during off-hours. Quick, satisfying, and available options are key. You know which places are open late and which items hit the spot when you\'re craving something.',
        'trend_chaser': 'You like trying new things and keeping up with food trends. You\'re among the first to try limited-time offers, new menu items, and viral food trends. Novelty and social media buzz influence your choices.',
        'family_bundle_buyer': 'You buy for a family, so value, variety, and family-friendly options matter. You look for deals that feed multiple people, kid-friendly options, and meals that everyone will enjoy.',
        'protein_maximizer': 'You focus on protein content and fitness goals. High-protein options are your priority, and you often choose items based on protein-to-calorie ratios. You might be into fitness, bodybuilding, or just want to feel full longer.',
    }
    
    archetype_desc = archetype_descriptions.get(agent.archetype, 'a typical consumer')
    
    return f"""You are {agent.display_name}, a {agent.age_bucket}-year-old {agent.gender.lower()} from {agent.region} with {agent.income} income.

**Your Behavioral Profile:**
You are {archetype_desc}.

**Your Background:**
- You live in {agent.region}
- Your income level is {agent.income}
- You're in the {agent.age_bucket} age range
- Your taste preferences include: {', '.join(agent.taste_profile_json[:5]) if agent.taste_profile_json else 'varied tastes'}

Respond naturally and authentically from this persona's perspective. Be specific about your preferences, habits, and decision-making process."""


def _categorize_hypothesis_question(hypothesis_text: str) -> str:
    """Categorize hypothesis question to provide appropriate prompts."""
    text_lower = hypothesis_text.lower()
    
    # Beauty questions
    if 'sephora' in text_lower or ('discover' in text_lower and 'beauty' in text_lower):
        return 'beauty_sephora'
    if 'virtual' in text_lower and 'beauty' in text_lower:
        return 'beauty_virtual'
    if 'fashion' in text_lower and ('cash back' in text_lower or 'app' in text_lower):
        return 'beauty_virtual'
    if 'beautify' in text_lower:
        return 'beauty_virtual'
    
    # Food questions
    if 'pricing' in text_lower and ('fast food' in text_lower or 'menu' in text_lower):
        return 'food_pricing'
    if 'price-sensitive' in text_lower or ('price' in text_lower and 'segment' in text_lower):
        return 'food_sensitivity'
    if 'cookie' in text_lower or ('cookie' in text_lower and 'preference' in text_lower):
        return 'food_cookie'
    if 'mcdonalds' in text_lower or 'burger king' in text_lower:
        return 'food_pricing'
    
    # AITANA questions
    if 'functional' in text_lower and ('food' in text_lower or 'snack' in text_lower):
        return 'aitana_food'
    if 'beauty' in text_lower and ('category' in text_lower or 'portfolio' in text_lower):
        return 'aitana_beauty'
    if 'prestige' in text_lower and 'beauty' in text_lower:
        return 'aitana_beauty'
    
    return 'generic'


def _build_enhanced_system_prompt(agent: PersonaAgent, question_category: str) -> str:
    """Build enhanced system prompt based on question category."""
    base_prompt = f"""You are a simulated consumer agent named {agent.display_name}.

Your persona:
- Archetype: {agent.get_archetype_display()}
- Age: {agent.age_bucket}
- Gender: {agent.gender}
- Region: {agent.region}
- Income: {agent.income}
- Behavioral traits: {json.dumps(agent.behavior_params_json, indent=2) if agent.behavior_params_json else '{}'}"""
    
    category_guidance = {
        'beauty_sephora': """
You are responding to questions about beauty product discovery and purchase decisions.
Consider: How you discover products (social media, in-store, reviews), what influences your purchases,
the importance of personalization, and factors that cause purchase delays or abandonment.
Be specific about your beauty shopping behaviors and preferences.""",
        
        'beauty_virtual': """
You are responding to questions about shifting from in-store to virtual beauty experiences.
Consider: What features would make you switch to virtual consultations, the importance of
AI matching, video consultations, AR try-on, and how your shopping habits would change.
Be specific about your preferences for in-store vs. virtual experiences.""",
        
        'food_pricing': """
You are responding to questions about fast-food pricing and menu structure.
Consider: Your price sensitivity, perception of value, preferences for combo meals vs. a la carte,
how pricing affects your purchase frequency, and what price points feel fair.
Be specific about your spending habits and price thresholds.""",
        
        'food_sensitivity': """
You are responding to questions about price sensitivity across customer segments.
Consider: How price changes affect your behavior, your willingness to pay premiums,
price thresholds that cause you to switch brands or reduce frequency, and how this varies
by occasion or time of day. Be specific about your price sensitivity.""",
        
        'food_cookie': """
You are responding to questions about cookie and packaged food preferences.
Consider: How your preferences are shifting (taste vs. health vs. price vs. convenience),
whether you're switching brands or changing consumption behavior, and how you perceive
different brands. Be specific about what attributes matter most to you.""",
        
        'aitana_food': """
You are responding to questions about emerging functional food needs and snacking trends.
Consider: New functional jobs you're hiring food for (mood, focus, sleep, gut health, social moments),
which ingredients/formats/rituals appeal to you, and how trends differ by your cohort.
Be specific about your functional food needs and usage occasions.""",
        
        'aitana_beauty': """
You are responding to questions about beauty category strategy and portfolio decisions.
Consider: Which beauty categories matter most to you, how demand is evolving across price tiers,
where you're trading up or down, competitor positioning, and latest innovation trends.
Be specific about your category preferences and price tier behaviors.""",
        
        'generic': """
Respond authentically to the hypothesis question based on your persona.
Be specific about your preferences, behaviors, and decision-making factors."""
    }
    
    guidance = category_guidance.get(question_category, category_guidance['generic'])
    return base_prompt + guidance


def _build_enhanced_user_prompt(agent: PersonaAgent, hypothesis_text: str, question_category: str) -> str:
    """Build enhanced user prompt with category-specific guidance."""
    base_prompt = f"""HYPOTHESIS QUESTION:
{hypothesis_text}

Based on your persona as {agent.display_name} ({agent.get_archetype_display()}, {agent.age_bucket}, {agent.region}),
provide a detailed, authentic response to this question.

IMPORTANT: Provide unique insights specific to your persona. Different agents should have different perspectives
based on their demographics, archetype, and behavioral traits. Be specific with examples, numbers, and concrete behaviors.

Respond in JSON format:
{{
  "agent_id": "{agent.id}",
  "decision": "your decision/preference/answer",
  "reasons": ["specific reason 1 with details", "specific reason 2 with details", "specific reason 3 with details"],
  "confidence": 0.75,
  "specific_examples": ["concrete example 1", "concrete example 2"],
  "data_points": {{"metric": "value", "another_metric": "value"}}
}}"""
    
    category_specific = {
        'beauty_sephora': """
Focus on: Discovery channels (TikTok, Instagram, in-store), influence factors (consultants vs. reviews vs. influencers),
personalization importance, abandonment reasons (price, availability, indecision). Include specific percentages or frequencies.""",
        
        'beauty_virtual': """
Focus on: Required features for virtual switch (AI matching accuracy, video quality, AR capabilities),
deal-breakers, price expectations, return policies. Be specific about what would make you switch.""",
        
        'food_pricing': """
Focus on: Price perception (too high/just right), value perception, preferred price ranges,
how pricing affects frequency, willingness to pay premiums. Include specific price points.""",
        
        'food_sensitivity': """
Focus on: Price sensitivity level, reaction to price changes, switching behavior,
frequency reduction, trade-down behavior. Include specific percentages or thresholds.""",
        
        'food_cookie': """
Focus on: Attribute importance (taste, health, price, convenience), brand switching,
consumption changes, brand perception vs. competitors. Be specific about trade-offs.""",
        
        'aitana_food': """
Focus on: Functional needs (mood, focus, sleep, gut health), preferred ingredients/formats,
usage occasions, cohort differences (Gen Z vs. Millennials). Include specific examples.""",
        
        'aitana_beauty': """
Focus on: Category priorities, price tier preferences, trading behavior, innovation interests,
competitor comparisons. Include specific categories and price points."""
    }
    
    additional = category_specific.get(question_category, "")
    return base_prompt + additional if additional else base_prompt


def _generate_gpt_response(
    agent: PersonaAgent,
    task_type: str,
    payload: Dict,
    agent_tron_context: Optional[Dict] = None
) -> Dict:
    """
    Generate response using GPT.
    
    Direct GPT-4 hypothesis generation (Agent-Tron/LPM/Data Engine unhooked).
    """
    if not client:
        return {
            'text': 'GPT client not available. Please set OPENAI_API_KEY environment variable.',
            'structured': {}
        }
    
    try:
        if task_type == 'chat':
            messages = payload.get('messages', [])
            
            # Build comprehensive system prompt with all agent details
            system_prompt = agent.system_prompt or _build_default_system_prompt(agent)
            
            # Enhance system prompt with additional context
            taste_prefs = ', '.join(agent.taste_profile_json or []) if agent.taste_profile_json else 'varied tastes'
            behavior_traits = json.dumps(agent.behavior_params_json, indent=2) if agent.behavior_params_json else '{}'
            
            enhanced_system_prompt = f"""{system_prompt}

**Your Persona Details:**
- Name: {agent.display_name}
- Age: {agent.age_bucket}
- Gender: {agent.gender}
- Region: {agent.region}
- Income: {agent.income}
- Behavioral Archetype: {agent.get_archetype_display()}
- Taste Preferences: {taste_prefs}
- Behavior Traits: {behavior_traits}

**Communication Style:**
- Respond naturally and conversationally as this persona
- Stay in character based on your archetype and demographics
- Keep responses authentic to your background and preferences
- Be specific about your preferences and behaviors
- Use casual, natural language appropriate for your age and background
- Reference your region, income level, and lifestyle when relevant

**Context:**
You're chatting with someone who wants to understand your preferences and behaviors regarding fast-food choices. Answer their questions authentically from your persona's perspective."""
            
            system_msg = {
                'role': 'system',
                'content': enhanced_system_prompt
            }
            
            # Convert user messages to OpenAI format
            gpt_messages = [system_msg]
            for msg in messages[-15:]:  # Last 15 messages for better context
                if isinstance(msg, dict):
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    if content and role in ['user', 'assistant']:
                        gpt_messages.append({
                            'role': role,
                            'content': content
                        })
                else:
                    # Handle string messages
                    gpt_messages.append({
                        'role': 'user',
                        'content': str(msg)
                    })
            
            print(f"[GPT] Calling OpenAI API for {agent.display_name} - Chat")
            print(f"[GPT] Messages count: {len(gpt_messages)}")
            print(f"[GPT] System prompt length: {len(gpt_messages[0]['content']) if gpt_messages else 0}")
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=gpt_messages,
                temperature=0.9,  # Higher temperature for more natural, varied responses
                max_tokens=400,   # More tokens for richer conversations
                presence_penalty=0.6,  # Encourage diverse responses
                frequency_penalty=0.3  # Reduce repetition
            )
            
            response_text = response.choices[0].message.content.strip()
            print(f"[GPT] Received response from OpenAI: {response_text[:100]}...")
            
            if not response_text:
                response_text = "I'm not sure how to respond to that. Could you rephrase?"
            
            return {
                'text': response_text,
                'structured': {}
            }
        
        elif task_type == 'hypothesis':
            # Direct GPT-4 hypothesis generation (Agent-Tron/LPM/Data Engine unhooked)
            
            hypothesis_text = payload.get('input_text', '')
            question_category = _categorize_hypothesis_question(hypothesis_text)
            
            # Build enhanced system prompt based on question category
            system_prompt = _build_enhanced_system_prompt(agent, question_category)
            
            # Build enhanced user prompt based on question category
            user_prompt = _build_enhanced_user_prompt(
                agent, hypothesis_text, question_category
            )
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                temperature=0.8,  # Higher temperature for more diverse, persona-specific responses
                max_tokens=500,  # Increased for more detailed responses
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                structured_response = json.loads(response_text)
                
                # Ensure required fields exist
                if 'decision' not in structured_response:
                    structured_response['decision'] = 'Neutral'
                if 'reasons' not in structured_response:
                    structured_response['reasons'] = []
                if 'confidence' not in structured_response:
                    structured_response['confidence'] = 0.7
                
                # Build text response from structured data
                decision = structured_response.get('decision', 'Neutral')
                reasons = structured_response.get('reasons', [])
                text_response = f"{decision}: {'; '.join(reasons) if reasons else 'No specific reasons provided.'}"
                
                return {
                    'text': text_response,
                    'structured': structured_response,
                }
            except json.JSONDecodeError:
                # Fallback: return text response if JSON parsing fails
                logger.warning(f"Failed to parse JSON response from GPT-4 for agent {agent.id}")
                return {
                    'text': response_text,
                    'structured': {
                        'decision': 'Neutral',
                        'reasons': [response_text],
                        'confidence': 0.5
                    },
                }
        
        elif task_type == 'survey':
            question = payload.get('question', '')
            question_type = payload.get('question_type', 'open')
            
            system_prompt = agent.system_prompt or f"""You are {agent.display_name}, a {agent.get_archetype_display()} from {agent.region}.
Age: {agent.age_bucket}, Gender: {agent.gender}, Income: {agent.income}
Behavioral traits: {json.dumps(agent.behavior_params_json)}"""
            
            if question_type == 'likert':
                user_prompt = f"""Answer this survey question on a scale of 1-5 (1=Strongly Disagree, 5=Strongly Agree):
{question}

Respond with just a number (1-5) and a brief explanation."""
            elif question_type == 'multiple_choice':
                user_prompt = f"""Answer this multiple choice question:
{question}

Provide your choice and a brief explanation."""
            else:
                user_prompt = f"""Answer this survey question:
{question}

Provide a brief, authentic response from your persona's perspective."""
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            return {
                'text': response.choices[0].message.content.strip(),
                'structured': {}
            }
        
        else:
            # Unknown task type - return error instead of mock
            return {
                'text': f"Unknown task type: {task_type}",
                'structured': {}
            }
    
    except Exception as e:
        print(f"GPT error for {agent.display_name} ({task_type}): {e}")
        import traceback
        traceback.print_exc()
        # Never fallback to mock - always return error message so user knows GPT failed
        error_details = str(e)
        if "API key" in error_details.lower() or "authentication" in error_details.lower():
            error_msg = "OpenAI API key is invalid or missing. Please check your OPENAI_API_KEY in backend/.env"
        elif "rate limit" in error_details.lower():
            error_msg = "OpenAI API rate limit exceeded. Please try again in a moment."
        elif "insufficient_quota" in error_details.lower():
            error_msg = "OpenAI API quota exceeded. Please check your OpenAI account billing."
        else:
            error_msg = f"GPT API error: {error_details}. Please check server logs for details."
        
        return {
            'text': f"⚠️ {error_msg}",
            'structured': {}
        }


def _generate_mock_response(agent: PersonaAgent, task_type: str, payload: Dict) -> Dict:
    """Generate deterministic mock response based on agent behavior params."""
    print(f"⚠️ WARNING: _generate_mock_response called for {agent.display_name} (task: {task_type}) - This should not happen when mode='gpt'!")
    params = agent.behavior_params_json
    archetype = agent.archetype
    
    if task_type == 'chat':
        user_message = payload.get('messages', [{}])[-1].get('content', '')
        return {
            'text': _mock_chat_response(agent, user_message),
            'structured': {}
        }
    
    elif task_type == 'hypothesis':
        input_text = payload.get('input_text', '').lower()
        return {
            'text': _mock_hypothesis_response(agent, input_text),
            'structured': {}
        }
    
    elif task_type == 'survey':
        question = payload.get('question', '')
        question_type = payload.get('question_type', 'open')
        return {
            'text': _mock_survey_response(agent, question, question_type),
            'structured': _mock_survey_structured(agent, question_type)
        }
    
    elif task_type == 'taste_test':
        items = payload.get('items', [])
        return {
            'text': _mock_taste_test_response(agent, items),
            'structured': _mock_taste_test_structured(agent, items)
        }
    
    return {'text': 'Mock response', 'structured': {}}


def _mock_chat_response(agent: PersonaAgent, user_message: str) -> str:
    """Generate mock chat response."""
    archetype_responses = {
        'value_seeker': "I'm always looking for the best deal. Price matters most to me.",
        'health_optimizer': "I care about nutrition and ingredients. Quality over convenience.",
        'convenience_loyalist': "I go with what's fast and reliable. Consistency is key.",
        'late_night_craver': "I'm usually ordering late at night. Need something quick and satisfying.",
        'trend_chaser': "I like trying new things and keeping up with trends.",
        'family_bundle_buyer': "I'm feeding a family, so value and variety matter.",
        'protein_maximizer': "I focus on protein content. That's my priority."
    }
    
    base_response = archetype_responses.get(agent.archetype, "That's interesting.")
    
    if 'price' in user_message.lower() or 'cost' in user_message.lower():
        if agent.archetype == 'value_seeker':
            return "Absolutely! Price is everything. I compare deals constantly."
        return base_response
    
    if 'health' in user_message.lower() or 'nutrition' in user_message.lower():
        if agent.archetype == 'health_optimizer':
            return "Yes, I always check nutrition facts. Ingredients matter to me."
        return base_response
    
    return base_response


def _mock_hypothesis_response(agent: PersonaAgent, input_text: str) -> str:
    """Generate mock hypothesis response."""
    params = agent.behavior_params_json
    archetype = agent.archetype
    
    if 'protein' in input_text:
        if archetype == 'protein_maximizer':
            return f"As a {agent.get_archetype_display()}, I'd definitely respond positively to high-protein campaigns. That's exactly what I look for."
        return f"I might notice it, but protein isn't my main concern."
    
    if 'gen z' in input_text or 'young' in input_text:
        if agent.age_bucket == '18-24':
            return f"As someone in Gen Z, I'd be interested if it feels authentic and relevant to my values."
        return f"I'm not in that demographic, so it might not resonate as much."
    
    if 'late night' in input_text:
        if archetype == 'late_night_craver':
            return f"Late-night options are crucial for me. I'd definitely increase visits if there were better options."
        return f"I don't usually eat late at night, so it wouldn't affect me much."
    
    # Default based on archetype
    sentiment = params.get('sentiment_bias', 0.5)
    if sentiment > 0.6:
        return f"As a {agent.get_archetype_display()}, I'd likely respond positively to this."
    elif sentiment < 0.4:
        return f"I'm skeptical about this. Doesn't align with my preferences."
    return f"I'd need to see more details, but it could be interesting."


def _mock_survey_response(agent: PersonaAgent, question: str, question_type: str) -> str:
    """Generate mock survey response."""
    if question_type == 'likert':
        params = agent.behavior_params_json
        base_score = params.get('sentiment_bias', 0.5)
        # Map to 1-5 scale
        score = int(base_score * 4) + 1
        return f"I'd rate it {score} out of 5."
    
    if question_type == 'multiple_choice':
        # Deterministic choice based on archetype
        choices = ['Option A', 'Option B', 'Option C']
        idx = hash(agent.id) % len(choices)
        return choices[idx]
    
    # Open ended
    return _mock_chat_response(agent, question)


def _mock_survey_structured(agent: PersonaAgent, question_type: str) -> Dict:
    """Generate structured survey response."""
    params = agent.behavior_params_json
    
    if question_type == 'likert':
        base_score = params.get('sentiment_bias', 0.5)
        score = int(base_score * 4) + 1
        return {'likert_score': score}
    
    if question_type == 'multiple_choice':
        choices = ['A', 'B', 'C']
        idx = hash(agent.id) % len(choices)
        return {'choice': choices[idx]}
    
    return {}


def _mock_taste_test_response(agent: PersonaAgent, items: List[str]) -> str:
    """Generate mock taste test response."""
    params = agent.behavior_params_json
    health_bias = params.get('health_bias', 0.5)
    
    # Prefer healthier options if health_optimizer
    if agent.archetype == 'health_optimizer' and 'Chipotle' in str(items):
        return "I'd prefer Chipotle - it feels fresher and healthier."
    
    # Prefer value options if value_seeker
    if agent.archetype == 'value_seeker' and 'McDonald' in str(items):
        return "McDonald's gives the best value for money."
    
    return f"I'd probably go with {items[0] if items else 'the first option'} based on my preferences."


def _mock_taste_test_structured(agent: PersonaAgent, items: List[str]) -> Dict:
    """Generate structured taste test ranking."""
    params = agent.behavior_params_json
    health_bias = params.get('health_bias', 0.5)
    
    # Create ranking based on archetype
    rankings = []
    for i, item in enumerate(items):
        score = 0.5
        if agent.archetype == 'health_optimizer' and 'Chipotle' in str(item):
            score = 0.9
        elif agent.archetype == 'value_seeker' and 'McDonald' in str(item):
            score = 0.9
        else:
            score = 0.5 + (hash(str(agent.id) + item) % 30) / 100
        
        rankings.append({'item': item, 'score': score})
    
    rankings.sort(key=lambda x: x['score'], reverse=True)
    return {'rankings': rankings}


def generate_gpt4_report(input_text: str, responses: List[Dict], agents_info: List[Dict]) -> Dict:
    """
    Generate a comprehensive GPT-4 report analyzing agent responses.
    Returns structured data including summary, insights, and chart data.
    """
    if not client:
        return {
            'error': 'GPT client not available. Please set OPENAI_API_KEY in backend/.env file.'
        }
    
    # Prepare agent responses summary for GPT
    responses_summary = []
    for i, resp in enumerate(responses[:50]):  # Limit to 50 for token efficiency
        agent_info = agents_info[i] if i < len(agents_info) else {}
        responses_summary.append({
            'agent': agent_info.get('name', f'Agent {i+1}'),
            'archetype': agent_info.get('archetype', 'unknown'),
            'demographics': f"{agent_info.get('age_bucket', 'N/A')} • {agent_info.get('region', 'N/A')}",
            'response': resp.get('text', '')[:200]  # Truncate long responses
        })
    
    # Build comprehensive prompt for GPT-4
    system_prompt = """You are an expert data analyst specializing in consumer behavior and market research. 
Analyze the provided agent responses to generate a comprehensive report with:
1. Executive summary (2-3 paragraphs)
2. Key findings and insights
3. Preference breakdown (if comparing brands/products)
4. Segment analysis (by archetype, demographics)
5. Top drivers and themes
6. Recommendations

Return your analysis as a structured JSON with the following format:
{
  "executive_summary": "2-3 paragraph summary",
  "key_findings": ["finding 1", "finding 2", ...],
  "preference_breakdown": {
    "mcdonalds": {"percentage": 45, "reasons": ["reason1", "reason2"]},
    "burger_king": {"percentage": 55, "reasons": ["reason1", "reason2"]}
  },
  "segment_insights": {
    "archetype": {
      "value_seeker": {"preference": "mcdonalds", "percentage": 60, "insight": "..."},
      ...
    },
    "age": {
      "18-24": {"preference": "burger_king", "percentage": 55, "insight": "..."},
      ...
    },
    "region": {
      "West": {"preference": "mcdonalds", "percentage": 52, "insight": "..."},
      ...
    }
  },
  "top_drivers": [
    {"theme": "price", "mentions": 45, "impact": "high"},
    {"theme": "taste", "mentions": 38, "impact": "high"},
    ...
  ],
  "recommendations": ["recommendation 1", "recommendation 2", ...],
  "overall_sentiment": 0.65,
  "confidence": 0.82
}

Extract brand/product names from the question and responses. Be specific and data-driven."""
    
    user_prompt = f"""Question/Hypothesis: {input_text}

Agent Responses ({len(responses)} total):
{json.dumps(responses_summary, indent=2)}

Analyze these responses and generate a comprehensive report. Extract preferences, themes, and insights. 
If comparing brands/products, provide clear preference breakdowns with percentages and reasons.
Include segment-level insights showing how different archetypes, age groups, and regions differ."""
    
    try:
        print(f"[GPT-4 Report] Generating comprehensive report for hypothesis: {input_text[:100]}...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        report_json = json.loads(response.choices[0].message.content)
        print(f"[GPT-4 Report] Generated report successfully")
        return report_json
        
    except Exception as e:
        print(f"[GPT-4 Report] Error generating report: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to basic aggregation
        return {'error': str(e)}


def aggregate_agent_responses(responses: List[Dict], task_type: str) -> Dict:
    """
    Aggregate multiple agent responses into summary statistics.
    
    🚨 For hypothesis tasks, uses Agent-Tron confidence metrics for weighting.
    """
    if not responses:
        return {}
    
    if task_type == 'hypothesis':
        sentiments = []
        themes = {}
        preferences = {}  # Track brand preferences
        confidences = []
        evidence_refs_all = []
        
        for resp in responses:
            # Use GPT confidence from structured response, or default to 0.7
            structured = resp.get('structured', {})
            confidence = structured.get('confidence', 0.7) if structured else 0.7
            confidences.append(confidence)
            
            if structured:
                # Use structured decision and confidence
                decision = structured.get('decision', '').lower()
                
                # Track brand preferences
                if 'mcdonalds' in decision or 'mcdonald' in decision:
                    preferences['mcdonalds'] = preferences.get('mcdonalds', 0) + 1
                    sentiment = 0.7
                elif 'burger king' in decision or 'bk' in decision:
                    preferences['burger_king'] = preferences.get('burger_king', 0) + 1
                    sentiment = 0.3
                elif 'neutral' in decision:
                    preferences['neutral'] = preferences.get('neutral', 0) + 1
                    sentiment = 0.5
                else:
                    # Fallback to text analysis
                    text = resp.get('text', '').lower()
                    if 'mcdonalds' in text or 'mcdonald' in text:
                        preferences['mcdonalds'] = preferences.get('mcdonalds', 0) + 1
                        sentiment = 0.7
                    elif 'burger king' in text or 'bk' in text:
                        preferences['burger_king'] = preferences.get('burger_king', 0) + 1
                        sentiment = 0.3
                    else:
                        preferences['neutral'] = preferences.get('neutral', 0) + 1
                        sentiment = 0.5
                
                sentiments.append(sentiment)
                
                # Collect evidence refs for traceability
                evidence_refs = structured.get('evidence_refs', [])
                evidence_refs_all.extend(evidence_refs)
                
                # Extract themes from reasons
                reasons = structured.get('reasons', [])
                for reason in reasons:
                    reason_lower = reason.lower()
                    if 'protein' in reason_lower:
                        themes['protein'] = themes.get('protein', 0) + 1
                    if 'price' in reason_lower or 'value' in reason_lower:
                        themes['value'] = themes.get('value', 0) + 1
                    if 'health' in reason_lower or 'nutrition' in reason_lower:
                        themes['health'] = themes.get('health', 0) + 1
            else:
                # Fallback to text analysis
                text = resp.get('text', '').lower()
                if 'mcdonalds' in text or 'mcdonald' in text:
                    preferences['mcdonalds'] = preferences.get('mcdonalds', 0) + 1
                    sentiment = 0.7
                elif 'burger king' in text or 'bk' in text:
                    preferences['burger_king'] = preferences.get('burger_king', 0) + 1
                    sentiment = 0.3
                else:
                    preferences['neutral'] = preferences.get('neutral', 0) + 1
                    sentiment = 0.5
                
                sentiments.append(sentiment)
                
                # Extract themes
                if 'protein' in text:
                    themes['protein'] = themes.get('protein', 0) + 1
                if 'price' in text or 'value' in text:
                    themes['value'] = themes.get('value', 0) + 1
                if 'health' in text or 'nutrition' in text:
                    themes['health'] = themes.get('health', 0) + 1
        
        # Calculate average sentiment
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.5
        
        # Calculate average confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.7
        
        # Calculate preference breakdown percentages
        total_responses = len(responses)
        preference_breakdown = {}
        if total_responses > 0:
            for brand, count in preferences.items():
                percentage = round((count / total_responses) * 100)
                preference_breakdown[brand] = {
                    'percentage': percentage,
                    'count': count,
                    'reasons': []  # Could extract from reasons if needed
                }
        
        return {
            'overall_sentiment': avg_sentiment,
            'confidence': avg_confidence,
            'preference_breakdown': preference_breakdown,  # Add preference breakdown
            'top_themes': dict(sorted(themes.items(), key=lambda x: x[1], reverse=True)[:5]),
            'response_count': len(responses),
            'distribution': {
                'positive': sum(1 for s in sentiments if s > 0.6),
                'neutral': sum(1 for s in sentiments if 0.4 <= s <= 0.6),
                'negative': sum(1 for s in sentiments if s < 0.4),
            },
            'evidence_traceability': {
                'unique_evidence_refs': len(set(evidence_refs_all)),
                'total_evidence_refs': len(evidence_refs_all),
            }
        }
    
    elif task_type == 'survey':
        # Aggregate survey responses
        scores = []
        choices = {}
        
        for resp in responses:
            structured = resp.get('structured', {})
            if 'likert_score' in structured:
                scores.append(structured['likert_score'])
            if 'choice' in structured:
                choice = structured['choice']
                choices[choice] = choices.get(choice, 0) + 1
        
        result = {
            'response_count': len(responses),
            'distribution': choices if choices else {},
        }
        
        if scores:
            result['average_score'] = sum(scores) / len(scores)
            result['score_distribution'] = {
                str(i): scores.count(i) for i in range(1, 6)
            }
        
        return result
    
    return {'response_count': len(responses)}

