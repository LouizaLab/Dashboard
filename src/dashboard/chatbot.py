"""
LLM-powered chatbot for dashboard insights
Provides conversational interface to understand data insights
"""

import os
from typing import Dict, List, Optional
import pandas as pd
import json

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class DashboardChatbot:
    """
    Chatbot that understands dashboard data and provides insights
    """
    
    def __init__(self, 
                 data: Dict[str, pd.DataFrame],
                 insights: List[Dict],
                 use_openai: bool = True,
                 model: str = "gpt-4o"):
        """
        Initialize chatbot with dashboard data
        
        Args:
            data: Dictionary of all dashboard dataframes
            insights: List of generated insights
            use_openai: If True, use OpenAI API; if False, use Anthropic
            model: Model name to use
        """
        self.data = data
        self.insights = insights
        self.use_openai = use_openai
        self.model = model
        self.conversation_history = []
        
        # Initialize API client
        if use_openai and OPENAI_AVAILABLE:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                from openai import OpenAI
                self.client = OpenAI(api_key=api_key)
                self.client_type = 'openai'
            else:
                self.client = None
                self.client_type = None
        elif not use_openai and ANTHROPIC_AVAILABLE:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                self.client = Anthropic(api_key=api_key)
                self.client_type = 'anthropic'
            else:
                self.client = None
                self.client_type = None
        else:
            self.client = None
            self.client_type = None
    
    def _prepare_data_summary(self) -> str:
        """Prepare a summary of all dashboard data for the LLM"""
        summary_parts = []
        
        # Products summary
        if not self.data['products'].empty:
            products = self.data['products']
            summary_parts.append(f"**Products**: {len(products)} products")
            if 'category' in products.columns:
                categories = products['category'].value_counts().to_dict()
                summary_parts.append(f"  Categories: {categories}")
        
        # Segments summary
        if not self.data['segments'].empty:
            segments = self.data['segments']
            summary_parts.append(f"**Segments**: {len(segments)} segments")
            if 'segment_id' in segments.columns:
                # Use psychographic as primary identifier
                if 'psychographic' in segments.columns:
                    segment_info = segments.apply(
                        lambda row: f"{row['psychographic'].title().replace('_', ' ')} ({row.get('age_bucket', '')}, {row.get('region', '')})" if pd.notna(row.get('psychographic')) else row['segment_id'],
                        axis=1
                    ).tolist()
                    summary_parts.append(f"  Segments: {segment_info}")
                elif 'segment_name' in segments.columns:
                    segment_names = segments.apply(
                        lambda row: f"{row['segment_name']} ({row['segment_id']})" if pd.notna(row.get('segment_name')) else row['segment_id'],
                        axis=1
                    ).tolist()
                    summary_parts.append(f"  Segments: {segment_names}")
                else:
                    summary_parts.append(f"  Segment IDs: {segments['segment_id'].tolist()}")
        
        # Trajectories summary
        if not self.data['trajectories'].empty:
            traj = self.data['trajectories']
            summary_parts.append(f"**Trajectories**: {len(traj)} interactions")
            if 'intent_value' in traj.columns:
                summary_parts.append(f"  Avg Intent: {traj['intent_value'].mean():.3f}")
                summary_parts.append(f"  Intent Range: [{traj['intent_value'].min():.3f}, {traj['intent_value'].max():.3f}]")
            if 'product_category' in traj.columns or 'category' in traj.columns:
                cat_col = 'product_category' if 'product_category' in traj.columns else 'category'
                cat_counts = traj[cat_col].value_counts().head(5).to_dict()
                summary_parts.append(f"  Top Categories: {cat_counts}")
        
        # Phase 4 anchored data
        if not self.data.get('phase4_anchored', pd.DataFrame()).empty:
            phase4 = self.data['phase4_anchored']
            summary_parts.append(f"**Phase 4 Anchored Data**: {len(phase4)} interactions")
            if 'intent_value' in phase4.columns:
                summary_parts.append(f"  Avg Intent: {phase4['intent_value'].mean():.3f}")
        
        # Intent index
        if not self.data.get('intent_index', pd.DataFrame()).empty:
            intent_idx = self.data['intent_index']
            summary_parts.append(f"**Intent Index**: {len(intent_idx)} data points")
            if 'intent_mean' in intent_idx.columns:
                summary_parts.append(f"  Avg Intent Mean: {intent_idx['intent_mean'].mean():.3f}")
        
        # Momentum
        if not self.data.get('momentum', pd.DataFrame()).empty:
            momentum = self.data['momentum']
            summary_parts.append(f"**Momentum Signals**: {len(momentum)} data points")
            if 'momentum' in momentum.columns:
                summary_parts.append(f"  Avg Momentum: {momentum['momentum'].mean():.3f}")
        
        # Insights summary
        if self.insights:
            summary_parts.append(f"**Generated Insights**: {len(self.insights)} insights")
            for i, insight in enumerate(self.insights[:5], 1):
                summary_parts.append(f"  {i}. {insight.get('title', 'Unknown')}: {insight.get('description', '')}")
        
        return "\n".join(summary_parts)
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for the LLM"""
        data_summary = self._prepare_data_summary()
        
        return f"""You are an expert data analyst chatbot helping users understand insights from a behavioral simulation dashboard.

**Dashboard Context:**
{data_summary}

**Your Role:**
- Answer questions about the data, insights, and patterns
- Explain what the metrics mean in business terms
- Help users understand behavioral trends
- Provide actionable insights based on the data
- Be conversational and helpful

**Available Data:**
- Products: Product metadata (categories, ingredients, nutrition, price)
- Segments: User segments (age, region, psychographics)
- Trajectories: Behavioral intent trajectories over time
- Phase 4 Anchored: Calibrated simulation data
- Intent Index: Category-level intent over time
- Momentum: Momentum signals for trends
- Insights: Auto-generated insight cards

**Key Metrics:**
- Intent Value: Purchase probability (0-1 scale)
- Purchase Probability: Likelihood of purchase
- Repeat Rate: Frequency of repeat purchases
- Churn Rate: Rate of low intent/attrition
- Adoption Rate: New product trial rate

Answer questions clearly and concisely. If asked about specific numbers, provide them if available in the context."""
    
    def chat(self, user_message: str) -> str:
        """
        Process user message and return chatbot response
        
        Args:
            user_message: User's question/message
            
        Returns:
            Chatbot response
        """
        if not self.client:
            return "⚠️ LLM API not configured. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable."
        
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # Prepare messages
        messages = [
            {"role": "system", "content": self._get_system_prompt()}
        ] + self.conversation_history[-10:]  # Keep last 10 messages for context
        
        try:
            if self.client_type == 'openai':
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=500
                )
                assistant_message = response.choices[0].message.content.strip()
            elif self.client_type == 'anthropic':
                # Convert messages format for Anthropic
                system_msg = messages[0]['content']
                conversation_msgs = messages[1:]
                
                response = self.client.messages.create(
                    model=self.model if 'claude' in self.model else 'claude-3-haiku-20240307',
                    max_tokens=500,
                    system=system_msg,
                    messages=conversation_msgs
                )
                assistant_message = response.content[0].text
            else:
                assistant_message = "LLM client not properly initialized."
            
            # Add assistant response to history
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            
            return assistant_message
            
        except Exception as e:
            return f"❌ Error: {str(e)}\n\nPlease check your API key and try again."
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []
    
    def get_suggested_questions(self) -> List[str]:
        """Get suggested questions users might ask"""
        return [
            "What are the key insights from the data?",
            "Which segment has the highest intent?",
            "What are the top product categories?",
            "How does intent change over time?",
            "What is the price sensitivity?",
            "Which categories show strong momentum?",
            "What are the substitution patterns?",
            "How does context affect intent?",
            "What is the repeat purchase rate?",
            "Compare Phase 3 vs Phase 4 results"
        ]

