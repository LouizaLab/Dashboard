"""
Management command to recalculate edge weights based on actual metrics.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Company, Edge
from api.edge_calculator import EdgeWeightCalculator


class Command(BaseCommand):
    help = 'Recalculate edge weights and factors based on actual company metrics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--lookback-days',
            type=int,
            default=90,
            help='Number of days to look back for calculations (default: 90)',
        )
        parser.add_argument(
            '--min-data-points',
            type=int,
            default=10,
            help='Minimum data points required for valid calculation (default: 10)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be calculated without saving',
        )

    def handle(self, *args, **options):
        lookback_days = options['lookback_days']
        min_data_points = options['min_data_points']
        dry_run = options['dry_run']
        
        self.stdout.write(f'Initializing edge weight calculator...')
        self.stdout.write(f'  Lookback days: {lookback_days}')
        self.stdout.write(f'  Minimum data points: {min_data_points}')
        
        calculator = EdgeWeightCalculator(
            lookback_days=lookback_days,
            min_data_points=min_data_points
        )
        
        companies = list(Company.objects.all())
        self.stdout.write(f'\nFound {len(companies)} companies')
        
        # Get all edges
        edges = Edge.objects.select_related('source_company', 'target_company').all()
        edge_count = edges.count()
        self.stdout.write(f'Found {edge_count} edges to recalculate\n')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be saved\n'))
        
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        with transaction.atomic():
            for i, edge in enumerate(edges, 1):
                try:
                    source = edge.source_company
                    target = edge.target_company
                    
                    self.stdout.write(
                        f'[{i}/{edge_count}] Calculating: {source.name} -> {target.name}',
                        ending=''
                    )
                    
                    # Calculate new weight and factors
                    weight, factors, matrix = calculator.compute_edge_weight(source, target)
                    
                    # Check if we have enough data
                    if weight == 0.0 and all(v == 0.0 for v in factors.values()):
                        self.stdout.write(' ... SKIPPED (insufficient data)')
                        skipped_count += 1
                        continue
                    
                    # Show changes
                    old_weight = edge.weight
                    weight_change = weight - old_weight
                    
                    self.stdout.write(
                        f' ... Weight: {old_weight:.3f} -> {weight:.3f} '
                        f'({weight_change:+.3f})'
                    )
                    
                    if not dry_run:
                        # Update edge
                        edge.weight = weight
                        edge.factors_json = factors
                        edge.matrix_json = matrix
                        edge.save()
                        updated_count += 1
                    else:
                        updated_count += 1
                        
                except Exception as e:
                    self.stdout.write(f' ... ERROR: {str(e)}')
                    error_count += 1
                    if not dry_run:
                        # Continue in transaction, but log error
                        self.stdout.write(self.style.ERROR(f'  Failed to update edge: {e}'))
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write('SUMMARY')
        self.stdout.write('='*60)
        self.stdout.write(f'Total edges processed: {edge_count}')
        self.stdout.write(f'Successfully updated: {updated_count}')
        self.stdout.write(f'Skipped (insufficient data): {skipped_count}')
        self.stdout.write(f'Errors: {error_count}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN - No changes were saved'))
            self.stdout.write('Run without --dry-run to apply changes')
        else:
            self.stdout.write(self.style.SUCCESS('\n✓ Edge recalculation complete!'))
