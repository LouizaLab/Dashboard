"""
Management command to rebuild market manifolds.
Usage: python manage.py rebuild_market_manifold --vertical beauty --region US --organic
"""
from django.core.management.base import BaseCommand
from api.market_insight_manifold import ManifoldBuilder
from api.market_insight_manifold_organic import OrganicManifoldBuilder


class Command(BaseCommand):
    help = 'Rebuild market manifold for a given vertical and region'

    def add_arguments(self, parser):
        parser.add_argument(
            '--vertical',
            type=str,
            default='beauty',
            help='Vertical (beauty or food)',
        )
        parser.add_argument(
            '--region',
            type=str,
            default='US',
            help='Region (default: US)',
        )
        parser.add_argument(
            '--organic',
            action='store_true',
            help='Use organic manifold builder (default: True)',
        )
        parser.add_argument(
            '--n-points',
            type=int,
            default=900,
            help='Number of points to generate (organic mode only)',
        )
        parser.add_argument(
            '--k-clusters',
            type=int,
            default=18,
            help='Number of clusters (organic mode only)',
        )
        parser.add_argument(
            '--seed',
            type=int,
            default=42,
            help='Random seed for reproducibility',
        )

    def handle(self, *args, **options):
        vertical = options['vertical']
        region = options['region']
        use_organic = options.get('organic', True)  # Default to organic
        
        self.stdout.write(f"Rebuilding manifold for {vertical}/{region}...")
        
        if use_organic:
            n_points = options.get('n_points', 900)
            k_clusters = options.get('k_clusters', 18)
            seed = options.get('seed', 42)
            
            self.stdout.write(f"Using organic manifold builder (n_points={n_points}, k_clusters={k_clusters}, seed={seed})")
            builder = OrganicManifoldBuilder(
                vertical=vertical, 
                region=region, 
                seed=seed,
                n_points=n_points,
                k_clusters=k_clusters
            )
            points, hulls, cluster_info = builder.build_organic_manifold(force_rebuild=True)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully rebuilt organic manifold: {points.count()} points, '
                    f'{len(cluster_info)} clusters, {len(hulls)} hulls'
                )
            )
        else:
            builder = ManifoldBuilder(vertical=vertical, region=region)
            points = builder.build_manifold(force_rebuild=True)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully rebuilt manifold: {points.count()} points'
                )
            )
