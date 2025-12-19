"""
Services for GPT integration and mock responses.
"""
import os
import json
import random
from typing import Dict, List, Optional
from .sim_models import PersonaAgent

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Initialize OpenAI client if API key is available
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') or os.environ.get('OPENAI_KEY')
client = None
if OPENAI_AVAILABLE and OPENAI_API_KEY:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception:
        client = None


def generate_persona_response(
    agent: PersonaAgent,
    task_type: str,
    payload: Dict,
    mode: str = 'mock'
) -> Dict:
    """
    Generate a persona response using GPT or mock.
    
    Args:
        agent: PersonaAgent instance
        task_type: 'hypothesis', 'survey', 'taste_test', 'chat'
        payload: Task-specific payload
        mode: 'gpt' or 'mock'
    
    Returns:
        Dict with 'text' and optionally 'structured' data
    """
    if mode == 'gpt' and client:
        return _generate_gpt_response(agent, task_type, payload)
    else:
        return _generate_mock_response(agent, task_type, payload)


def _generate_gpt_response(agent: PersonaAgent, task_type: str, payload: Dict) -> Dict:
    """Generate response using GPT."""
    try:
        if task_type == 'chat':
            messages = payload.get('messages', [])
            # Convert to OpenAI format
            system_msg = {
                'role': 'system',
                'content': agent.system_prompt
            }
            
            # Convert user messages to OpenAI format
            gpt_messages = [system_msg]
            for msg in messages[-10:]:  # Last 10 messages for context
                if isinstance(msg, dict):
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    if role in ['user', 'assistant']:
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
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=gpt_messages,
                temperature=0.8,
                max_tokens=300
            )
            return {
                'text': response.choices[0].message.content.strip(),
                'structured': {}
            }
        
        elif task_type == 'hypothesis':
            # For hypothesis, create a compact prompt
            prompt = f"""As {agent.display_name}, a {agent.get_archetype_display()} from {agent.region}, 
            respond to this hypothesis: {payload.get('input_text', '')}
            
            Consider your demographics: {agent.age_bucket}, {agent.gender}, {agent.income}
            Your behavioral traits: {json.dumps(agent.behavior_params_json)}
            
            Provide a brief response (2-3 sentences) from your persona's perspective."""
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.8,
                max_tokens=150
            )
            return {
                'text': response.choices[0].message.content,
                'structured': {}
            }
        
        elif task_type == 'survey':
            question = payload.get('question', '')
            prompt = f"""As {agent.display_name}, answer this survey question: {question}
            
            Your persona: {agent.get_archetype_display()}, {agent.age_bucket}, {agent.region}
            Provide a brief, authentic response."""
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.7,
                max_tokens=100
            )
            return {
                'text': response.choices[0].message.content,
                'structured': {}
            }
        
        else:
            return _generate_mock_response(agent, task_type, payload)
    
    except Exception as e:
        print(f"GPT error: {e}")
        return _generate_mock_response(agent, task_type, payload)


def _generate_mock_response(agent: PersonaAgent, task_type: str, payload: Dict) -> Dict:
    """Generate deterministic mock response based on agent behavior params."""
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


def aggregate_agent_responses(responses: List[Dict], task_type: str) -> Dict:
    """Aggregate multiple agent responses into summary statistics."""
    if not responses:
        return {}
    
    if task_type == 'hypothesis':
        sentiments = []
        themes = {}
        
        for resp in responses:
            text = resp.get('text', '').lower()
            # Simple sentiment scoring
            positive_words = ['yes', 'would', 'like', 'prefer', 'good', 'great', 'definitely']
            negative_words = ['no', 'wouldn\'t', 'don\'t', 'not', 'bad', 'skeptical']
            
            pos_count = sum(1 for w in positive_words if w in text)
            neg_count = sum(1 for w in negative_words if w in text)
            
            sentiment = 0.5
            if pos_count > neg_count:
                sentiment = 0.6 + (pos_count - neg_count) * 0.1
            elif neg_count > pos_count:
                sentiment = 0.4 - (neg_count - pos_count) * 0.1
            
            sentiments.append(sentiment)
            
            # Extract themes
            if 'protein' in text:
                themes['protein'] = themes.get('protein', 0) + 1
            if 'price' in text or 'value' in text:
                themes['value'] = themes.get('value', 0) + 1
            if 'health' in text or 'nutrition' in text:
                themes['health'] = themes.get('health', 0) + 1
        
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.5
        
        return {
            'overall_sentiment': avg_sentiment,
            'confidence': min(0.95, 0.6 + len(responses) / 200),
            'top_themes': dict(sorted(themes.items(), key=lambda x: x[1], reverse=True)[:5]),
            'response_count': len(responses),
            'distribution': {
                'positive': sum(1 for s in sentiments if s > 0.6),
                'neutral': sum(1 for s in sentiments if 0.4 <= s <= 0.6),
                'negative': sum(1 for s in sentiments if s < 0.4),
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

