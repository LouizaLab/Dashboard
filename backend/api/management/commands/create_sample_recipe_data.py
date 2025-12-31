"""
Management command to create sample recipe variants and approval personas.
Run with: python manage.py create_sample_recipe_data
"""
from django.core.management.base import BaseCommand
from api.recipe_models import RecipeVariant, ApprovalPersona


class Command(BaseCommand):
    help = 'Creates sample recipe variants and approval personas'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample approval personas...')
        
        # Create approval personas if they don't exist
        personas_data = [
            {
                'persona_type': 'consumer_insights_head',
                'name': 'Consumer Insights Head',
                'taste_acceptance_threshold': 0.65,
                'price_sensitivity_threshold': 0.4,
                'health_acceptance_threshold': 0.6,
                'cannibalization_risk_threshold': 0.25,
                'demographic_coverage_threshold': 0.6,
                'substitution_risk_threshold': 0.35,
                'risk_tolerance': 0.5,
                'factor_weights_json': {
                    'taste': 0.3,
                    'price': 0.2,
                    'health': 0.25,
                    'demographics': 0.25
                }
            },
            {
                'persona_type': 'regulatory_affairs',
                'name': 'Regulatory Affairs Manager',
                'taste_acceptance_threshold': 0.5,
                'price_sensitivity_threshold': 0.6,
                'health_acceptance_threshold': 0.7,
                'cannibalization_risk_threshold': 0.4,
                'demographic_coverage_threshold': 0.5,
                'substitution_risk_threshold': 0.5,
                'risk_tolerance': 0.3,
                'factor_weights_json': {
                    'taste': 0.2,
                    'price': 0.1,
                    'health': 0.4,
                    'regulatory': 0.3
                }
            },
            {
                'persona_type': 'brand_manager',
                'name': 'Brand Manager',
                'taste_acceptance_threshold': 0.7,
                'price_sensitivity_threshold': 0.5,
                'health_acceptance_threshold': 0.5,
                'cannibalization_risk_threshold': 0.2,
                'demographic_coverage_threshold': 0.7,
                'substitution_risk_threshold': 0.3,
                'risk_tolerance': 0.6,
                'factor_weights_json': {
                    'taste': 0.35,
                    'price': 0.15,
                    'brand': 0.3,
                    'demographics': 0.2
                }
            },
            {
                'persona_type': 'finance_forecasting',
                'name': 'Finance / Forecasting',
                'taste_acceptance_threshold': 0.6,
                'price_sensitivity_threshold': 0.3,
                'health_acceptance_threshold': 0.5,
                'cannibalization_risk_threshold': 0.3,
                'demographic_coverage_threshold': 0.6,
                'substitution_risk_threshold': 0.4,
                'risk_tolerance': 0.4,
                'factor_weights_json': {
                    'taste': 0.2,
                    'price': 0.4,
                    'revenue': 0.3,
                    'forecast': 0.1
                }
            }
        ]
        
        for persona_data in personas_data:
            persona, created = ApprovalPersona.objects.get_or_create(
                persona_type=persona_data['persona_type'],
                defaults=persona_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created persona: {persona.name}'))
            else:
                self.stdout.write(f'Persona already exists: {persona.name}')
        
        self.stdout.write('\nCreating sample recipe variants...')
        
        # Create sample recipe variants
        variants_data = [
            {
                'name': 'Low Sodium Burger',
                'base_product_id': 'burger_001',
                'base_product_name': 'Classic Burger',
                'nutrition_delta_json': {
                    'calories': 0,
                    'sugar': 0,
                    'fat': 0,
                    'sodium': -15.0,
                    'protein': 0
                },
                'sensory_delta_json': {
                    'sweetness': 0,
                    'saltiness': -0.2,
                    'texture': 0,
                    'heat': 0,
                    'aroma': 0
                },
                'price_delta': 0.0,
                'ingredient_changes_json': {
                    'added': [],
                    'removed': [],
                    'substituted': {'regular_salt': 'low_sodium_salt'}
                },
                'positioning_tags_json': ['healthy', 'low_sodium'],
                'description': 'Reduced sodium version of classic burger'
            },
            {
                'name': 'Reduced Sugar Cookie',
                'base_product_id': 'cookie_001',
                'base_product_name': 'Chocolate Chip Cookie',
                'nutrition_delta_json': {
                    'calories': -5.0,
                    'sugar': -20.0,
                    'fat': 0,
                    'sodium': 0,
                    'protein': 0
                },
                'sensory_delta_json': {
                    'sweetness': -0.15,
                    'saltiness': 0,
                    'texture': 0.05,
                    'heat': 0,
                    'aroma': 0
                },
                'price_delta': 0.0,
                'ingredient_changes_json': {
                    'added': [],
                    'removed': [],
                    'substituted': {'sugar': 'stevia'}
                },
                'positioning_tags_json': ['healthy', 'low_sugar'],
                'description': 'Reduced sugar version using natural sweetener'
            },
            {
                'name': 'Premium Burger (+$0.50)',
                'base_product_id': 'burger_001',
                'base_product_name': 'Classic Burger',
                'nutrition_delta_json': {
                    'calories': 50.0,
                    'sugar': 0,
                    'fat': 5.0,
                    'sodium': 0,
                    'protein': 5.0
                },
                'sensory_delta_json': {
                    'sweetness': 0,
                    'saltiness': 0,
                    'texture': 0.1,
                    'heat': 0,
                    'aroma': 0.15
                },
                'price_delta': 0.50,
                'ingredient_changes_json': {
                    'added': ['premium_cheese', 'artisan_bun'],
                    'removed': [],
                    'substituted': {}
                },
                'positioning_tags_json': ['premium', 'indulgent'],
                'description': 'Premium version with upgraded ingredients and higher price'
            }
        ]
        
        for variant_data in variants_data:
            variant, created = RecipeVariant.objects.get_or_create(
                name=variant_data['name'],
                base_product_id=variant_data['base_product_id'],
                defaults=variant_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created variant: {variant.name}'))
            else:
                self.stdout.write(f'Variant already exists: {variant.name}')
        
        self.stdout.write(self.style.SUCCESS('\nSample data creation complete!'))

