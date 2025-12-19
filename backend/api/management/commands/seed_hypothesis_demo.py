"""
Management command to seed hypothesis testing demo data.
"""
import random
import json
import math
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from api.sim_models import PersonaAgent, SurveyQuestion, EvidenceSurveyDatum

class Command(BaseCommand):
    help = 'Seed demo data for hypothesis testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--agents',
            type=int,
            default=150,
            help='Number of agents to create',
        )

    def handle(self, *args, **options):
        random.seed(42)  # Deterministic seed
        num_agents = options['agents']
        
        self.stdout.write('Creating persona agents...')
        self._create_agents(num_agents)
        
        self.stdout.write('Creating survey questions...')
        self._create_survey_questions()
        
        self.stdout.write('Creating evidence survey data...')
        self._create_evidence_data()
        
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully seeded hypothesis demo data!'))
        self.stdout.write(f'  Agents: {num_agents}')
        self.stdout.write(f'  Survey questions: 20')
        self.stdout.write(f'  Evidence snippets: 200')

    def _create_agents(self, count):
        """Create persona agents."""
        archetypes = [
            'value_seeker', 'health_optimizer', 'convenience_loyalist',
            'late_night_craver', 'trend_chaser', 'family_bundle_buyer', 'protein_maximizer'
        ]
        age_buckets = ['18-24', '25-34', '35-44', '45-54', '55+']
        genders = ['Male', 'Female', 'Nonbinary', 'Prefer not to say']
        regions = ['West', 'Midwest', 'South', 'Northeast']
        incomes = ['$0-50k', '$50-100k', '$100-150k', '$150k+']
        
        first_names = [
            'Alex', 'Jordan', 'Taylor', 'Morgan', 'Casey', 'Riley', 'Avery', 'Quinn',
            'Sam', 'Dakota', 'Blake', 'Cameron', 'Drew', 'Emery', 'Finley', 'Hayden',
            'Jamie', 'Kai', 'Logan', 'Parker', 'Reese', 'Sage', 'Skyler', 'Tyler'
        ]
        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
            'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Wilson', 'Anderson', 'Thomas', 'Taylor'
        ]
        
        taste_tags = [
            'spicy', 'sweet', 'savory', 'crispy', 'fresh', 'bold', 'mild', 'rich',
            'light', 'hearty', 'tangy', 'smoky', 'creamy', 'crunchy'
        ]
        
        created = 0
        for i in range(count):
            archetype = random.choice(archetypes)
            age_bucket = random.choice(age_buckets)
            gender = random.choice(genders)
            region = random.choice(regions)
            income = random.choice(incomes)
            
            display_name = f"{random.choice(first_names)} {random.choice(last_names)}"
            
            # Generate behavior params based on archetype
            behavior_params = self._generate_behavior_params(archetype)
            
            # Generate taste profile (3-5 tags)
            num_tags = random.randint(3, 5)
            taste_profile = random.sample(taste_tags, num_tags)
            
            # Generate system prompt
            system_prompt = self._generate_system_prompt(display_name, archetype, age_bucket, gender, region, income, behavior_params)
            
            # Generate biography
            biography = self._generate_biography(display_name, archetype, age_bucket, region)
            
            agent, was_created = PersonaAgent.objects.get_or_create(
                display_name=display_name,
                defaults={
                    'age_bucket': age_bucket,
                    'gender': gender,
                    'region': region,
                    'income': income,
                    'archetype': archetype,
                    'taste_profile_json': taste_profile,
                    'behavior_params_json': behavior_params,
                    'system_prompt': system_prompt,
                    'biography': biography,
                }
            )
            
            if was_created:
                created += 1
        
        self.stdout.write(f'  Created {created} agents')

    def _generate_behavior_params(self, archetype):
        """Generate behavior parameters for archetype."""
        base_params = {
            'price_sensitivity': random.uniform(0.3, 0.7),
            'health_bias': random.uniform(0.3, 0.7),
            'brand_loyalty': random.uniform(0.3, 0.7),
            'novelty_seeking': random.uniform(0.3, 0.7),
            'convenience_priority': random.uniform(0.3, 0.7),
            'sentiment_bias': random.uniform(0.4, 0.6),
        }
        
        # Adjust based on archetype
        if archetype == 'value_seeker':
            base_params['price_sensitivity'] = random.uniform(0.7, 0.95)
            base_params['brand_loyalty'] = random.uniform(0.2, 0.5)
        elif archetype == 'health_optimizer':
            base_params['health_bias'] = random.uniform(0.7, 0.95)
            base_params['price_sensitivity'] = random.uniform(0.4, 0.6)
        elif archetype == 'convenience_loyalist':
            base_params['convenience_priority'] = random.uniform(0.7, 0.95)
            base_params['brand_loyalty'] = random.uniform(0.6, 0.9)
        elif archetype == 'late_night_craver':
            base_params['convenience_priority'] = random.uniform(0.7, 0.9)
            base_params['novelty_seeking'] = random.uniform(0.5, 0.7)
        elif archetype == 'trend_chaser':
            base_params['novelty_seeking'] = random.uniform(0.7, 0.95)
            base_params['brand_loyalty'] = random.uniform(0.3, 0.5)
        elif archetype == 'family_bundle_buyer':
            base_params['price_sensitivity'] = random.uniform(0.6, 0.8)
            base_params['convenience_priority'] = random.uniform(0.6, 0.8)
        elif archetype == 'protein_maximizer':
            base_params['health_bias'] = random.uniform(0.6, 0.8)
            base_params['novelty_seeking'] = random.uniform(0.4, 0.6)
        
        return base_params

    def _generate_system_prompt(self, name, archetype, age, gender, region, income, params):
        """Generate GPT system prompt."""
        archetype_desc = {
            'value_seeker': 'You prioritize getting the best value and deals. Price is your main concern.',
            'health_optimizer': 'You focus on nutrition and healthy options. Ingredients and nutritional value matter most.',
            'convenience_loyalist': 'You value speed and reliability. You stick with brands you know work.',
            'late_night_craver': 'You often order food late at night. Quick, satisfying options are key.',
            'trend_chaser': 'You like trying new things and keeping up with food trends.',
            'family_bundle_buyer': 'You buy for a family. Value, variety, and family-friendly options matter.',
            'protein_maximizer': 'You focus on protein content. High-protein options are your priority.',
        }
        
        return f"""You are {name}, a {age} {gender} from {region} with {income} income.
You are a {archetype_desc.get(archetype, 'typical consumer')}.
Respond naturally and authentically from this persona's perspective. Keep responses concise (1-3 sentences)."""

    def _generate_biography(self, name, archetype, age, region):
        """Generate short biography."""
        archetype_bios = {
            'value_seeker': f"{name} is always hunting for deals and comparing prices. They know every promotion and coupon.",
            'health_optimizer': f"{name} reads nutrition labels carefully and prioritizes fresh, wholesome ingredients.",
            'convenience_loyalist': f"{name} values speed and consistency. They stick with what works.",
            'late_night_craver': f"{name} often orders food after 9pm. Quick, satisfying options are essential.",
            'trend_chaser': f"{name} loves trying new menu items and keeping up with food trends.",
            'family_bundle_buyer': f"{name} shops for a family, looking for value and variety.",
            'protein_maximizer': f"{name} focuses on protein content and looks for high-protein options.",
        }
        return archetype_bios.get(archetype, f"{name} is a typical fast-food consumer from {region}.")

    def _create_survey_questions(self):
        """Create survey questions."""
        questions_data = [
            {
                'text': 'How likely are you to try a new fast-food item?',
                'type': 'likert',
                'choices': ['1 - Very Unlikely', '2', '3', '4', '5 - Very Likely']
            },
            {
                'text': 'What matters most when choosing fast food?',
                'type': 'multiple_choice',
                'choices': ['Price', 'Taste', 'Health', 'Convenience', 'Brand']
            },
            {
                'text': 'How often do you visit fast-food restaurants?',
                'type': 'likert',
                'choices': ['1 - Rarely', '2', '3', '4', '5 - Very Often']
            },
            {
                'text': 'What time of day do you most often order fast food?',
                'type': 'multiple_choice',
                'choices': ['Breakfast', 'Lunch', 'Dinner', 'Late Night', 'Anytime']
            },
            {
                'text': 'How important is protein content in your food choices?',
                'type': 'likert',
                'choices': ['1 - Not Important', '2', '3', '4', '5 - Very Important']
            },
            {
                'text': 'Describe your ideal fast-food meal.',
                'type': 'open',
                'choices': []
            },
            {
                'text': 'Would you pay more for healthier fast-food options?',
                'type': 'likert',
                'choices': ['1 - Definitely Not', '2', '3', '4', '5 - Definitely Yes']
            },
            {
                'text': 'Which factor influences your brand choice most?',
                'type': 'multiple_choice',
                'choices': ['Price', 'Location', 'Menu Variety', 'Brand Reputation', 'Speed']
            },
            {
                'text': 'How do you feel about limited-time menu items?',
                'type': 'open',
                'choices': []
            },
            {
                'text': 'Rate your satisfaction with current fast-food options.',
                'type': 'likert',
                'choices': ['1 - Very Dissatisfied', '2', '3', '4', '5 - Very Satisfied']
            },
            {
                'text': 'What would make you visit a fast-food restaurant more often?',
                'type': 'open',
                'choices': []
            },
            {
                'text': 'How important are promotions and deals?',
                'type': 'likert',
                'choices': ['1 - Not Important', '2', '3', '4', '5 - Very Important']
            },
            {
                'text': 'Which meal type do you prefer?',
                'type': 'multiple_choice',
                'choices': ['Burgers', 'Chicken', 'Mexican', 'Asian', 'Salads', 'Other']
            },
            {
                'text': 'How do you discover new fast-food options?',
                'type': 'multiple_choice',
                'choices': ['Social Media', 'Friends', 'Ads', 'Walking By', 'App', 'Other']
            },
            {
                'text': 'Rate the importance of food freshness.',
                'type': 'likert',
                'choices': ['1 - Not Important', '2', '3', '4', '5 - Very Important']
            },
            {
                'text': 'What frustrates you most about fast food?',
                'type': 'open',
                'choices': []
            },
            {
                'text': 'How likely are you to order delivery vs dine-in?',
                'type': 'likert',
                'choices': ['1 - Always Dine-In', '2', '3', '4', '5 - Always Delivery']
            },
            {
                'text': 'Which dietary preference applies to you?',
                'type': 'multiple_choice',
                'choices': ['None', 'Vegetarian', 'Vegan', 'Gluten-Free', 'Keto', 'Other']
            },
            {
                'text': 'How important is speed of service?',
                'type': 'likert',
                'choices': ['1 - Not Important', '2', '3', '4', '5 - Very Important']
            },
            {
                'text': 'What would improve your fast-food experience?',
                'type': 'open',
                'choices': []
            },
        ]
        
        created = 0
        for q_data in questions_data:
            question, was_created = SurveyQuestion.objects.get_or_create(
                question_text=q_data['text'],
                defaults={
                    'question_type': q_data['type'],
                    'choices_json': q_data['choices'],
                }
            )
            if was_created:
                created += 1
        
        self.stdout.write(f'  Created {created} survey questions')

    def _create_evidence_data(self):
        """Create evidence survey data."""
        regions = ['West', 'Midwest', 'South', 'Northeast']
        archetypes = [
            'value_seeker', 'health_optimizer', 'convenience_loyalist',
            'late_night_craver', 'trend_chaser', 'family_bundle_buyer', 'protein_maximizer'
        ]
        
        snippets = [
            "I always check for deals before ordering. Price is everything.",
            "I look for fresh ingredients and nutritional info. Health matters to me.",
            "I stick with what I know works. Consistency is key.",
            "Late night cravings hit hard. I need something quick and satisfying.",
            "I love trying new menu items. Always looking for the latest trend.",
            "Feeding a family means finding value. Bundle deals are my go-to.",
            "Protein content is my priority. I check macros before ordering.",
            "I compare prices across apps. Best deal wins.",
            "I read ingredient lists carefully. No artificial stuff for me.",
            "Speed matters when I'm in a rush. Drive-thru is essential.",
        ]
        
        questions = [
            "How important is price when choosing fast food?",
            "What influences your fast-food choices most?",
            "How often do you try new fast-food items?",
            "What time do you most often order fast food?",
            "How important is protein content?",
            "Would you pay more for healthier options?",
            "What makes you choose one brand over another?",
            "How do you discover new fast-food options?",
        ]
        
        created = 0
        start_date = date.today() - timedelta(days=180)
        
        for i in range(200):
            region = random.choice(regions)
            archetype = random.choice(archetypes) if random.random() > 0.3 else ''
            question_text = random.choice(questions)
            snippet = random.choice(snippets)
            
            # Generate distribution
            distribution = {
                'strongly_agree': random.randint(10, 30),
                'agree': random.randint(20, 40),
                'neutral': random.randint(10, 25),
                'disagree': random.randint(5, 20),
                'strongly_disagree': random.randint(5, 15),
            }
            
            # Generate date
            days_ago = random.randint(0, 180)
            evidence_date = start_date + timedelta(days=days_ago)
            
            # Generate metadata
            sample_size = random.randint(150, 500)
            metadata = {
                'sample_size': sample_size,
                'confidence_level': random.choice([0.90, 0.95, 0.99]),
                'margin_of_error': round(random.uniform(3.0, 5.0), 1),
            }
            
            datum, was_created = EvidenceSurveyDatum.objects.get_or_create(
                question_text=question_text,
                region=region,
                date=evidence_date,
                defaults={
                    'archetype': archetype,
                    'snippet_text': snippet,
                    'distribution_json': distribution,
                    'metadata_json': metadata,
                }
            )
            
            if was_created:
                created += 1
        
        self.stdout.write(f'  Created {created} evidence snippets')

