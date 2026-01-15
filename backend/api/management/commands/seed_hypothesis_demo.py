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
            'ingredient_purist', 'clean_beauty_believer', 'clinical_results_seeker',
            'luxury_ritualist', 'trend_driven_experimenter', 'problem_solution_buyer',
            'sensitive_skin_minimalist', 'makeup_maximalist', 'skinimalist',
            'ethical_buyer', 'deal_hunter', 'pro_guided_buyer',
            'age_preventive_optimizer', 'routine_loyalist', 'fragrance_identity_buyer'
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
        if archetype == 'ingredient_purist':
            base_params['health_bias'] = random.uniform(0.8, 0.95)
            base_params['brand_loyalty'] = random.uniform(0.3, 0.6)
        elif archetype == 'clean_beauty_believer':
            base_params['health_bias'] = random.uniform(0.7, 0.9)
            base_params['price_sensitivity'] = random.uniform(0.4, 0.6)
        elif archetype == 'clinical_results_seeker':
            base_params['health_bias'] = random.uniform(0.8, 0.95)
            base_params['brand_loyalty'] = random.uniform(0.6, 0.9)
        elif archetype == 'luxury_ritualist':
            base_params['price_sensitivity'] = random.uniform(0.2, 0.4)
            base_params['brand_loyalty'] = random.uniform(0.7, 0.9)
        elif archetype == 'trend_driven_experimenter':
            base_params['novelty_seeking'] = random.uniform(0.8, 0.95)
            base_params['brand_loyalty'] = random.uniform(0.2, 0.5)
        elif archetype == 'problem_solution_buyer':
            base_params['health_bias'] = random.uniform(0.6, 0.8)
            base_params['novelty_seeking'] = random.uniform(0.4, 0.6)
        elif archetype == 'sensitive_skin_minimalist':
            base_params['health_bias'] = random.uniform(0.7, 0.9)
            base_params['brand_loyalty'] = random.uniform(0.7, 0.9)
        elif archetype == 'makeup_maximalist':
            base_params['novelty_seeking'] = random.uniform(0.7, 0.9)
            base_params['brand_loyalty'] = random.uniform(0.4, 0.7)
        elif archetype == 'skinimalist':
            base_params['convenience_priority'] = random.uniform(0.7, 0.9)
            base_params['novelty_seeking'] = random.uniform(0.3, 0.5)
        elif archetype == 'ethical_buyer':
            base_params['health_bias'] = random.uniform(0.6, 0.8)
            base_params['brand_loyalty'] = random.uniform(0.5, 0.8)
        elif archetype == 'deal_hunter':
            base_params['price_sensitivity'] = random.uniform(0.8, 0.95)
            base_params['brand_loyalty'] = random.uniform(0.2, 0.5)
        elif archetype == 'pro_guided_buyer':
            base_params['brand_loyalty'] = random.uniform(0.7, 0.9)
            base_params['health_bias'] = random.uniform(0.6, 0.8)
        elif archetype == 'age_preventive_optimizer':
            base_params['health_bias'] = random.uniform(0.7, 0.9)
            base_params['brand_loyalty'] = random.uniform(0.5, 0.8)
        elif archetype == 'routine_loyalist':
            base_params['brand_loyalty'] = random.uniform(0.8, 0.95)
            base_params['novelty_seeking'] = random.uniform(0.2, 0.4)
        elif archetype == 'fragrance_identity_buyer':
            base_params['brand_loyalty'] = random.uniform(0.7, 0.9)
            base_params['price_sensitivity'] = random.uniform(0.3, 0.6)

        return base_params

    def _generate_system_prompt(self, name, archetype, age, gender, region, income, params):
        """Generate GPT system prompt."""
        archetype_desc = {
            'ingredient_purist': 'You shop by actives, percentages, and formulations. You read ingredient lists carefully and prioritize products with specific active ingredients at effective concentrations. Transparency and scientific formulation matter most to you.',
            'clean_beauty_believer': 'You prioritize non-toxic, "clean" labels and avoid ingredients you perceive as harmful. You trust brands that align with clean beauty standards and are willing to pay more for products that meet your safety criteria.',
            'clinical_results_seeker': 'You only trust derm-backed, proven efficacy. Clinical studies, dermatologist recommendations, and evidence-based results are essential. You avoid unproven claims and prefer products with scientific backing.',
            'luxury_ritualist': 'You view premium beauty as self-care. High-end products are part of your wellness routine. You invest in quality, enjoy the experience, and see beauty products as a form of self-indulgence and care.',
            'trend_driven_experimenter': 'You chase viral products and have fast churn. Social media trends, influencer recommendations, and new launches excite you. You\'re always trying the latest thing and move on quickly to the next trend.',
            'problem_solution_buyer': 'You buy to fix specific skin or hair issues. You target products that address your particular concerns - acne, dryness, fine lines, etc. Results-oriented and problem-focused in your purchasing decisions.',
            'sensitive_skin_minimalist': 'You prefer low-irritation products and stick to a few trusted items. You avoid fragrances, harsh actives, and complex formulations. Simplicity and gentleness are your priorities.',
            'makeup_maximalist': 'You love bold looks and frequent launches. You experiment with color, technique, and new products regularly. Makeup is creative expression and you enjoy trying new trends and collections.',
            'skinimalist': 'You prefer sheer, minimal, multi-use products. Less is more - you want products that do multiple things and keep your routine simple. Natural finishes and versatile formulations appeal to you.',
            'ethical_buyer': 'You prioritize sustainability and values-led purchasing. Cruelty-free, eco-friendly packaging, ethical sourcing, and brand values matter as much as product performance. You support brands that align with your ethics.',
            'deal_hunter': 'You\'re sales-driven and price sensitive. You wait for discounts, use coupons, buy during sales, and compare prices across retailers. Value matters more than brand loyalty or premium positioning.',
            'pro_guided_buyer': 'You follow artists, dermatologists, and experts. Professional recommendations guide your purchases. You trust licensed professionals and their product suggestions over marketing or trends.',
            'age_preventive_optimizer': 'You focus on early anti-aging prevention. You start early with preventative skincare, invest in proven anti-aging ingredients, and take a proactive approach to maintaining youthful skin.',
            'routine_loyalist': 'You repeat the same regimen long-term. Once you find products that work, you stick with them. You\'re resistant to change and prefer consistency over experimentation.',
            'fragrance_identity_buyer': 'You see scent as your personal signature. Fragrance is deeply personal and you invest in scents that reflect your identity. You may have signature scents and view fragrance as essential self-expression.',
        }

        # Build persona traits from behavior params
        persona_traits = []
        if params.get('price_sensitivity', 0.5) > 0.7:
            persona_traits.append('very price-conscious')
        if params.get('health_bias', 0.5) > 0.7:
            persona_traits.append('health-focused')
        if params.get('brand_loyalty', 0.5) > 0.7:
            persona_traits.append('loyal to favorite brands')
        if params.get('novelty_seeking', 0.5) > 0.7:
            persona_traits.append('enjoys trying new things')

        traits_text = f" You are also {', '.join(persona_traits)}." if persona_traits else ""

        return f"""You are {name}, a {age}-year-old {gender.lower()} from {region} with {income} income.

**Your Behavioral Profile:**
{archetype_desc.get(archetype, 'You are a typical consumer.')}{traits_text}

**Your Communication Style:**
- Respond naturally and conversationally as this persona
- Stay in character based on your archetype and demographics
- Keep responses authentic to your background and preferences
- Be specific about your preferences, habits, and decision-making
- Use casual, natural language appropriate for your age group
- Reference your region, income level, and lifestyle when relevant

**Context:**
You're participating in conversations about beauty and skincare preferences, behaviors, and choices. Answer questions authentically from your persona's perspective, drawing on your archetype traits and personal background."""

    def _generate_biography(self, name, archetype, age, region):
        """Generate short biography."""
        archetype_bios = {
            'ingredient_purist': f"{name} shops by actives and formulations, reading ingredient lists carefully.",
            'clean_beauty_believer': f"{name} prioritizes clean, non-toxic beauty products and avoids harmful ingredients.",
            'clinical_results_seeker': f"{name} only trusts derm-backed products with proven clinical results.",
            'luxury_ritualist': f"{name} views premium beauty as essential self-care and wellness.",
            'trend_driven_experimenter': f"{name} chases viral products and loves trying new launches.",
            'problem_solution_buyer': f"{name} buys products to fix specific skin or hair concerns.",
            'sensitive_skin_minimalist': f"{name} prefers gentle, minimal products for sensitive skin.",
            'makeup_maximalist': f"{name} loves bold looks and experimenting with new makeup trends.",
            'skinimalist': f"{name} prefers simple, multi-use products and keeps routines minimal.",
            'ethical_buyer': f"{name} prioritizes sustainability and values-led beauty purchases.",
            'deal_hunter': f"{name} is sales-driven and always looks for the best beauty deals.",
            'pro_guided_buyer': f"{name} follows dermatologists and makeup artists for recommendations.",
            'age_preventive_optimizer': f"{name} focuses on early anti-aging prevention and proactive skincare.",
            'routine_loyalist': f"{name} sticks with the same beauty regimen long-term.",
            'fragrance_identity_buyer': f"{name} sees fragrance as a personal signature and invests in signature scents.",
        }
        return archetype_bios.get(archetype, f"{name} is a typical beauty consumer from {region}.")

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
