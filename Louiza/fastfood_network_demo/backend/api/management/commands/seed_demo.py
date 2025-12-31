"""
Management command to seed demo data.
"""
import random
import json
import math
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from api.models import Company, CompanyMetricPoint, Edge


class Command(BaseCommand):
    help = 'Seed demo data for fast-food network dashboard'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days of historical data to generate',
        )

    def handle(self, *args, **options):
        days = options['days']
        random.seed(42)  # Deterministic seed
        
        self.stdout.write('Creating companies...')
        companies_data = [
            {'name': "McDonald's", 'symbol': 'MCD', 'description': 'Fast-food burger chain'},
            {'name': 'Burger King', 'symbol': 'BKW', 'description': 'Flame-grilled burgers'},
            {'name': "Wendy's", 'symbol': 'WEN', 'description': 'Fresh, never frozen'},
            {'name': 'Taco Bell', 'symbol': 'TACO', 'description': 'Mexican-inspired fast food'},
            {'name': 'KFC', 'symbol': 'KFC', 'description': 'Fried chicken'},
            {'name': 'Chipotle', 'symbol': 'CMG', 'description': 'Fast-casual Mexican'},
            {'name': 'Subway', 'symbol': 'SUB', 'description': 'Sandwich chain'},
        ]
        
        companies = {}
        for comp_data in companies_data:
            company, created = Company.objects.get_or_create(
                name=comp_data['name'],
                defaults=comp_data
            )
            companies[comp_data['name']] = company
            if created:
                self.stdout.write(f'  Created: {company.name}')
        
        self.stdout.write('Generating time series data...')
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        metric_names = ['foot_traffic', 'revenue', 'intent_index', 'taste_index', 'sentiment_proxy']
        
        # Base values per company (for deterministic generation)
        base_values = {
            "McDonald's": {'foot_traffic': 1000, 'revenue': 5000, 'intent_index': 0.7, 'taste_index': 0.65},
            'Burger King': {'foot_traffic': 800, 'revenue': 4000, 'intent_index': 0.6, 'taste_index': 0.6},
            "Wendy's": {'foot_traffic': 600, 'revenue': 3000, 'intent_index': 0.55, 'taste_index': 0.58},
            'Taco Bell': {'foot_traffic': 700, 'revenue': 3500, 'intent_index': 0.65, 'taste_index': 0.62},
            'KFC': {'foot_traffic': 650, 'revenue': 3200, 'intent_index': 0.58, 'taste_index': 0.59},
            'Chipotle': {'foot_traffic': 550, 'revenue': 2800, 'intent_index': 0.72, 'taste_index': 0.75},
            'Subway': {'foot_traffic': 500, 'revenue': 2500, 'intent_index': 0.5, 'taste_index': 0.52},
        }
        
        created_count = 0
        current_date = start_date
        while current_date <= end_date:
            for company_name, company in companies.items():
                base = base_values.get(company_name, {})
                
                # Generate deterministic but varied values
                day_offset = (current_date - start_date).days
                random.seed(42 + hash(company_name) + day_offset)
                
                for metric_name in metric_names:
                    if metric_name in base:
                        base_val = base[metric_name]
                        # Add trend and noise
                        trend = 0.02 * random.random() - 0.01  # Small trend
                        noise = random.gauss(0, 0.1)  # Gaussian noise
                        weekly_pattern = 0.05 * math.sin(day_offset / 7 * 2 * 3.14159)
                        value = base_val * (1 + trend * day_offset + noise + weekly_pattern)
                    else:
                        # For sentiment_proxy, generate between -1 and 1
                        value = random.uniform(-0.5, 0.5)
                    
                    # Create segment data (dummy demographics)
                    segment_json = {
                        'age_bucket': random.choice(['18-24', '25-34', '35-44', '45-54', '55+']),
                        'income': random.choice(['low', 'medium', 'high']),
                        'region': random.choice(['northeast', 'south', 'midwest', 'west']),
                    }
                    
                    metric, created = CompanyMetricPoint.objects.get_or_create(
                        company=company,
                        date=current_date,
                        metric_name=metric_name,
                        defaults={
                            'value': value,
                            'segment_json': segment_json,
                        }
                    )
                    if created:
                        created_count += 1
            
            current_date += timedelta(days=1)
        
        self.stdout.write(f'  Created {created_count} metric points')
        
        self.stdout.write('Creating edges...')
        # Create edges between companies
        company_list = list(companies.values())
        edge_count = 0
        
        # Define relationship strengths (deterministic)
        relationships = {
            ("McDonald's", 'Burger King'): 0.85,
            ("McDonald's", "Wendy's"): 0.75,
            ('Burger King', "Wendy's"): 0.80,
            ('Taco Bell', 'KFC'): 0.70,
            ('Taco Bell', 'Chipotle'): 0.65,
            ('KFC', 'Chipotle'): 0.60,
            ("McDonald's", 'Taco Bell'): 0.50,
            ('Burger King', 'Taco Bell'): 0.48,
            ("Wendy's", 'Taco Bell'): 0.45,
            ('Subway', 'Chipotle'): 0.55,
            ('Subway', "McDonald's"): 0.40,
        }
        
        # Create bidirectional edges for all pairs
        for i, source in enumerate(company_list):
            for target in company_list[i+1:]:
                pair_key = (source.name, target.name)
                reverse_key = (target.name, source.name)
                
                # Get weight from relationships or generate
                if pair_key in relationships:
                    weight = relationships[pair_key]
                elif reverse_key in relationships:
                    weight = relationships[reverse_key]
                else:
                    # Generate based on similarity
                    weight = random.uniform(0.3, 0.7)
                
                # Generate factors
                factors = {
                    'taste_similarity': weight * random.uniform(0.8, 1.2),
                    'intent_overlap': weight * random.uniform(0.7, 1.1),
                    'foot_traffic_correlation': weight * random.uniform(0.6, 1.0),
                    'revenue_correlation': weight * random.uniform(0.65, 1.05),
                    'substitution_likelihood': weight * random.uniform(0.5, 0.9),
                    'co_visit_probability': weight * random.uniform(0.4, 0.8),
                    'brand_adjacency': weight * random.uniform(0.6, 1.0),
                }
                
                # Generate 3x3 matrix
                matrix = [
                    [random.uniform(0.1, 0.9) for _ in range(3)]
                    for _ in range(3)
                ]
                
                edge, created = Edge.objects.get_or_create(
                    source_company=source,
                    target_company=target,
                    defaults={
                        'weight': weight,
                        'factors_json': factors,
                        'matrix_json': matrix,
                    }
                )
                if created:
                    edge_count += 1
        
        self.stdout.write(f'  Created {edge_count} edges')
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully seeded demo data!'))
        self.stdout.write(f'  Companies: {len(companies)}')
        self.stdout.write(f'  Metric points: {created_count}')
        self.stdout.write(f'  Edges: {edge_count}')

