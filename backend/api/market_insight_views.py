"""
API views for Market Insight feature.
Provides endpoints for manifold visualization, node details, question answering, and scenario analysis.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .market_insight_models import (
    MarketDefinition, Brand, Product, MarketSignal, InnovationEvent,
    ManifoldPoint, InsightQuery, InsightAnswer
)
from .market_insight_manifold import ManifoldBuilder
from .market_insight_manifold_organic import OrganicManifoldBuilder
from .market_insight_engine import InsightEngine
from .market_insight_seed import seed_all
from .market_insight_simulator import MarketSimulator
from .market_insight_gpt import generate_insight_from_simulation
from .market_insight_models import MarketSimRun, MarketSimResult, MarketInsightAnswer
import json
import uuid


class MarketInsightViewSet(viewsets.ViewSet):
    """ViewSet for Market Insight endpoints."""
    
    @action(detail=False, methods=['get'])
    def manifold(self, request):
        """
        GET /api/market-insight-new/manifold?vertical=beauty&region=US&view=markets
        
        Returns manifold points + metadata for rendering 3D scatter plot.
        """
        vertical = request.query_params.get('vertical', 'beauty')
        region = request.query_params.get('region', 'US')
        view = request.query_params.get('view', 'all')  # all, markets, brands, products
        force_rebuild = request.query_params.get('rebuild', 'false').lower() == 'true'
        use_organic = request.query_params.get('organic', 'true').lower() == 'true'  # Default to organic
        
        # Build manifold - use organic builder for better clustering
        if use_organic:
            builder = OrganicManifoldBuilder(vertical=vertical, region=region, seed=42, n_points=900, k_clusters=18)
            result = builder.build_organic_manifold(force_rebuild=force_rebuild)
            if isinstance(result, tuple) and len(result) == 3:
                points, hulls, cluster_info = result
            else:
                # Fallback if return format is unexpected
                points = result if hasattr(result, 'filter') else ManifoldPoint.objects.none()
                hulls = {}
                cluster_info = {}
        else:
            builder = ManifoldBuilder(vertical=vertical, region=region)
            points = builder.build_manifold(force_rebuild=force_rebuild)
            hulls = {}
            cluster_info = {}
        
        # Filter by view if specified
        if view != 'all':
            points = points.filter(node_type=view.rstrip('s'))  # Remove plural
        
        # Serialize points
        manifold_data = []
        for point in points:
            # Get node details
            node_label = ""
            node_details = {}
            
            if point.node_type == 'market':
                try:
                    market = MarketDefinition.objects.get(id=point.node_id)
                    node_label = market.name
                    node_details = {
                        'category': market.category,
                        'sub_category': market.sub_category,
                        'price_tier': market.price_tier,
                        'tier': market.price_tier,
                    }
                    # Get momentum from recent signals
                    recent_signal = MarketSignal.objects.filter(market=market).order_by('-date').first()
                    if recent_signal:
                        node_details['momentum'] = recent_signal.trend_momentum or 0.0
                    else:
                        node_details['momentum'] = 0.0
                except MarketDefinition.DoesNotExist:
                    # Synthetic point - use cluster info for label and details
                    node_label = point.cluster_label or f"Market {str(point.node_id)[:8]}"
                    # Extract category/tier from cluster_label if possible
                    cluster_label = point.cluster_label or ''
                    if 'Skincare' in cluster_label:
                        node_details['category'] = 'Skincare'
                    elif 'Makeup' in cluster_label:
                        node_details['category'] = 'Makeup'
                    elif 'Fragrance' in cluster_label:
                        node_details['category'] = 'Fragrance'
                    elif 'Hair' in cluster_label:
                        node_details['category'] = 'Hair'
                    else:
                        node_details['category'] = 'Unknown'
                    
                    # Extract tier from cluster_label
                    if 'Ultra-Luxury' in cluster_label or 'Ultra-Lux' in cluster_label:
                        node_details['tier'] = 'ultra_luxury'
                        node_details['price_tier'] = 'ultra_luxury'
                    elif 'Super-Premium' in cluster_label or 'Super Premium' in cluster_label:
                        node_details['tier'] = 'super_premium'
                        node_details['price_tier'] = 'super_premium'
                    elif 'Premium' in cluster_label:
                        node_details['tier'] = 'premium'
                        node_details['price_tier'] = 'premium'
                    elif 'Entry-Premium' in cluster_label or 'Entry Premium' in cluster_label:
                        node_details['tier'] = 'entry_premium'
                        node_details['price_tier'] = 'entry_premium'
                    else:
                        node_details['tier'] = 'premium'
                        node_details['price_tier'] = 'premium'
                    
                    node_details['momentum'] = 0.0  # Default for synthetic points
            
            elif point.node_type == 'brand':
                try:
                    brand = Brand.objects.get(id=point.node_id)
                    node_label = brand.name
                    node_details = {
                        'brand_type': brand.brand_type,
                        'tier': brand.brand_type,
                    }
                    node_details['momentum'] = 0.0  # Brands don't have signals
                except Brand.DoesNotExist:
                    continue
            
            elif point.node_type == 'product':
                try:
                    product = Product.objects.get(id=point.node_id)
                    node_label = f"{product.brand.name} - {product.name}"
                    node_details = {
                        'category': product.category,
                        'price_tier': product.price_tier,
                        'tier': product.price_tier,
                    }
                    node_details['momentum'] = 0.0
                except Product.DoesNotExist:
                    continue
            
            manifold_data.append({
                'id': str(point.node_id),
                'type': point.node_type,
                'label': node_label,
                'x': point.x,
                'y': point.y,
                'z': point.z if hasattr(point, 'z') else 0.0,
                'cluster_id': point.cluster_id,
                'cluster_label': point.cluster_label,
                'reactivity_score': point.reactivity_score if hasattr(point, 'reactivity_score') else None,
                **node_details,
            })
        
        # Aggregate cluster information from points if cluster_info is empty
        if not cluster_info:
            # Build cluster_info from points
            from django.db.models import Count
            cluster_counts = {}
            cluster_labels = {}
            for point in points:
                if point.cluster_id is not None:
                    cid = point.cluster_id
                    if cid not in cluster_counts:
                        cluster_counts[cid] = 0
                        cluster_labels[cid] = point.cluster_label or f'Cluster {cid}'
                    cluster_counts[cid] += 1
            
            cluster_info = {
                cid: {
                    'label': cluster_labels[cid],
                    'count': cluster_counts[cid],
                    'drivers': {},
                }
                for cid in cluster_counts
            }
        
        # Aggregate cluster information
        clusters = []
        for cluster_id, info in cluster_info.items():
            clusters.append({
                'cluster_id': cluster_id,
                'label': info.get('label', f'Cluster {cluster_id}'),
                'count': info.get('count', 0),
                'drivers': info.get('drivers', {}),
            })
        
        # Convert hulls to serializable format
        hulls_data = {}
        for cid, hull_points in hulls.items():
            hulls_data[int(cid)] = hull_points.tolist() if hasattr(hull_points, 'tolist') else hull_points
        
        return Response({
            'points': manifold_data,
            'clusters': clusters,
            'hulls': hulls_data,  # Cluster boundaries
            'vertical': vertical,
            'region': region,
            'count': len(manifold_data),
        })
    
    @action(detail=False, methods=['get'], url_path='node/(?P<node_type>[^/.]+)/(?P<node_id>[^/.]+)')
    def node_detail(self, request, node_type=None, node_id=None):
        """
        GET /api/market-insight/node/<type>/<id>
        
        Returns full node details for side panel.
        """
        try:
            if node_type == 'market':
                market = MarketDefinition.objects.get(id=node_id)
                
                # Get signals
                signals = MarketSignal.objects.filter(market=market).order_by('-date')[:12]
                signals_data = [{
                    'date': s.date.isoformat(),
                    'intent_index': s.intent_index,
                    'trend_momentum': s.trend_momentum,
                    'price_elasticity_proxy': s.price_elasticity_proxy,
                    'social_velocity': s.social_velocity,
                } for s in signals]
                
                # Get innovation events
                events = InnovationEvent.objects.filter(market=market).order_by('-date')[:10]
                events_data = [{
                    'date': e.date.isoformat(),
                    'event_type': e.event_type,
                    'brand_name': e.brand.name if e.brand else None,
                    'innovation_tags': e.innovation_tags,
                    'description': e.description,
                } for e in events]
                
                # Get competitor brands
                competitor_brands = []
                if market.competitor_set:
                    brands = Brand.objects.filter(id__in=market.competitor_set)
                    competitor_brands = [{
                        'id': str(b.id),
                        'name': b.name,
                        'brand_type': b.brand_type,
                    } for b in brands]
                
                return Response({
                    'type': 'market',
                    'id': str(market.id),
                    'name': market.name,
                    'category': market.category,
                    'sub_category': market.sub_category,
                    'price_tier': market.price_tier,
                    'channel_mix': market.channel_mix,
                    'tags': market.tags,
                    'signals': signals_data,
                    'innovation_events': events_data,
                    'competitor_brands': competitor_brands,
                })
            
            elif node_type == 'brand':
                brand = Brand.objects.get(id=node_id)
                
                # Get products
                products = Product.objects.filter(brand=brand)[:20]
                products_data = [{
                    'id': str(p.id),
                    'name': p.name,
                    'category': p.category,
                    'price': float(p.price) if p.price else None,
                    'price_tier': p.price_tier,
                    'claims': p.claims,
                    'format': p.format,
                } for p in products]
                
                # Get innovation events
                events = InnovationEvent.objects.filter(brand=brand).order_by('-date')[:10]
                events_data = [{
                    'date': e.date.isoformat(),
                    'event_type': e.event_type,
                    'market_name': e.market.name if e.market else None,
                    'innovation_tags': e.innovation_tags,
                } for e in events]
                
                return Response({
                    'type': 'brand',
                    'id': str(brand.id),
                    'name': brand.name,
                    'brand_type': brand.brand_type,
                    'positioning_tags': brand.positioning_tags,
                    'products': products_data,
                    'innovation_events': events_data,
                })
            
            elif node_type == 'product':
                product = Product.objects.get(id=node_id)
                
                return Response({
                    'type': 'product',
                    'id': str(product.id),
                    'name': product.name,
                    'brand_name': product.brand.name,
                    'category': product.category,
                    'sub_category': product.sub_category,
                    'price': float(product.price) if product.price else None,
                    'price_tier': product.price_tier,
                    'claims': product.claims,
                    'format': product.format,
                    'ingredients': product.ingredients,
                    'launch_date': product.launch_date.isoformat() if product.launch_date else None,
                    'channel': product.channel,
                    'is_bundle': product.is_bundle,
                    'is_kit': product.is_kit,
                })
            
            else:
                return Response(
                    {'error': f'Unknown node type: {node_type}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except (MarketDefinition.DoesNotExist, Brand.DoesNotExist, Product.DoesNotExist):
            return Response(
                {'error': f'{node_type} with id {node_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def simulate(self, request):
        """
        POST /api/market-insight-new/simulate
        
        Run market simulation:
        {
            "question": "...",
            "vertical": "beauty",
            "region": "US",
            "pinned_nodes": [...],
            "filters": {...},
            "scenario_params": {
                "price_tier_shift": "...",
                "channel_shift": "...",
                "claim_emphasis": "...",
                "bundle_vs_single": "..."
            }
        }
        
        Returns SimulationResult.
        """
        question = request.data.get('question', '')
        vertical = request.data.get('vertical', 'beauty')
        region = request.data.get('region', 'US')
        pinned_nodes = request.data.get('pinned_nodes', [])
        filters = request.data.get('filters', {})
        scenario_params = request.data.get('scenario_params', {})
        seed = request.data.get('seed', 42)
        
        if not question:
            return Response(
                {'error': 'question is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create sim run
        sim_run = MarketSimRun.objects.create(
            question=question,
            vertical=vertical,
            region=region,
            scenario_params=scenario_params,
            filters=filters,
            pinned_nodes=pinned_nodes,
            seed=seed,
        )
        
        # Run simulation
        simulator = MarketSimulator(seed=seed)
        sim_result_data = simulator.simulate_market_impact(
            question=question,
            vertical=vertical,
            region=region,
            pinned_nodes=pinned_nodes,
            filters=filters,
            scenario_params=scenario_params,
        )
        
        # Store result
        sim_result = MarketSimResult.objects.create(
            sim_run=sim_run,
            impacted_clusters=sim_result_data['impacted_clusters'],
            impacted_points=sim_result_data['impacted_points'],
            category_tier_shifts=sim_result_data['category_tier_shifts'],
            competitor_positioning=sim_result_data['competitor_positioning'],
            innovation_patterns=sim_result_data['innovation_patterns'],
            confidence_score=sim_result_data['confidence_score'],
            entropy_score=sim_result_data['entropy_score'],
        )
        
        # Update reactivity scores on manifold points
        for point_data in sim_result_data['impacted_points']:
            ManifoldPoint.objects.filter(
                node_id=point_data['node_id'],
                vertical=vertical,
                region=region
            ).update(reactivity_score=point_data['reactivity_score'])
        
        return Response({
            'run_id': str(sim_run.id),
            'result_id': str(sim_result.id),
            **sim_result_data,
        })
    
    @action(detail=False, methods=['post'])
    def insight(self, request):
        """
        POST /api/market-insight-new/insight
        
        Generate GPT insight from simulation:
        {
            "result_id": "...",
            "question": "...",
            "vertical": "beauty",
            "region": "US",
            "pinned_nodes": [...],
            "scenario_params": {...}
        }
        
        Returns structured JSON insight.
        """
        result_id = request.data.get('result_id')
        question = request.data.get('question', '')
        vertical = request.data.get('vertical', 'beauty')
        region = request.data.get('region', 'US')
        pinned_nodes = request.data.get('pinned_nodes', [])
        scenario_params = request.data.get('scenario_params', {})
        
        if not result_id:
            return Response(
                {'error': 'result_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            sim_result = MarketSimResult.objects.get(id=result_id)
        except MarketSimResult.DoesNotExist:
            return Response(
                {'error': 'Simulation result not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Generate insight
        # Check if user wants to force GPT (via query param or request data)
        force_gpt = request.query_params.get('force_gpt', 'false').lower() == 'true' or request.data.get('force_gpt', False)
        insight_json = generate_insight_from_simulation(
            sim_result=sim_result,
            question=question,
            vertical=vertical,
            region=region,
            pinned_nodes=pinned_nodes,
            scenario_params=scenario_params,
            force_gpt=force_gpt,
        )
        
        # Combine results - return both simulation and insight
        return Response({
            'simulation': {
                'run_id': str(sim_run.id),
                'result_id': str(sim_result.id),
                **sim_result_data,
            },
            'insight': insight_json,
        })
    
    @action(detail=False, methods=['post'])
    def ask(self, request):
        """
        POST /api/market-insight-new/ask
        
        Full pipeline: simulate → insight
        
        Payload:
        {
            "vertical": "beauty",
            "region": "US",
            "question": "What categories should we prioritize?",
            "pinned_nodes": [...],
            "filters": {...},
            "scenario_params": {...}
        }
        
        Returns structured JSON answer.
        """
        vertical = request.data.get('vertical', 'beauty')
        region = request.data.get('region', 'US')
        question = request.data.get('question', '')
        pinned_nodes = request.data.get('pinned_nodes', [])
        filters = request.data.get('filters', {})
        scenario_params = request.data.get('scenario_params', {})
        seed = request.data.get('seed', 42)
        
        if not question:
            return Response(
                {'error': 'question is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Step 1: Run simulation
        sim_run = MarketSimRun.objects.create(
            question=question,
            vertical=vertical,
            region=region,
            scenario_params=scenario_params,
            filters=filters,
            pinned_nodes=pinned_nodes,
            seed=seed,
        )
        
        simulator = MarketSimulator(seed=seed)
        sim_result_data = simulator.simulate_market_impact(
            question=question,
            vertical=vertical,
            region=region,
            pinned_nodes=pinned_nodes,
            filters=filters,
            scenario_params=scenario_params,
        )
        
        sim_result = MarketSimResult.objects.create(
            sim_run=sim_run,
            impacted_clusters=sim_result_data['impacted_clusters'],
            impacted_points=sim_result_data['impacted_points'],
            category_tier_shifts=sim_result_data['category_tier_shifts'],
            competitor_positioning=sim_result_data['competitor_positioning'],
            innovation_patterns=sim_result_data['innovation_patterns'],
            confidence_score=sim_result_data['confidence_score'],
            entropy_score=sim_result_data['entropy_score'],
        )
        
        # Update reactivity scores
        for point_data in sim_result_data['impacted_points']:
            ManifoldPoint.objects.filter(
                node_id=point_data['node_id'],
                vertical=vertical,
                region=region
            ).update(reactivity_score=point_data['reactivity_score'])
        
        # Step 2: Fetch manifold data for comprehensive insights
        manifold_data = None
        try:
            from .market_insight_manifold_organic import OrganicManifoldBuilder
            builder = OrganicManifoldBuilder(vertical=vertical, region=region, seed=seed, n_points=900, k_clusters=18)
            points_qs, hulls, cluster_info = builder.build_organic_manifold(force_rebuild=False)
            
            # Get cluster information
            clusters_list = []
            for cid, info in cluster_info.items():
                clusters_list.append({
                    'cluster_id': cid,
                    'label': info.get('label', f'Cluster {cid}'),
                    'count': info.get('count', 0),
                    'drivers': info.get('drivers', {}),
                })
            
            # Get sample points (limit for prompt size)
            sample_points = []
            for point in points_qs[:100]:  # Limit to 100 points for prompt
                sample_points.append({
                    'id': str(point.node_id),
                    'label': point.cluster_label or f'Point {point.node_id}',
                    'cluster_id': point.cluster_id,
                    'cluster_label': point.cluster_label,
                    'x': point.x,
                    'y': point.y,
                    'z': point.z,
                })
            
            manifold_data = {
                'clusters': clusters_list,
                'points': sample_points,
                'total_points': points_qs.count(),
            }
            print(f"[Market Insight] Fetched manifold data: {len(clusters_list)} clusters, {len(sample_points)} sample points")
        except Exception as e:
            print(f"[Market Insight] Warning: Could not fetch manifold data: {e}")
            import traceback
            traceback.print_exc()
            manifold_data = None
        
        # Step 3: Generate insight
        # Check if user wants to force GPT
        force_gpt = request.query_params.get('force_gpt', 'false').lower() == 'true' or request.data.get('force_gpt', False)
        insight_json = generate_insight_from_simulation(
            sim_result=sim_result,
            question=question,
            vertical=vertical,
            region=region,
            pinned_nodes=pinned_nodes,
            scenario_params=scenario_params,
            force_gpt=force_gpt,
            manifold_data=manifold_data,
        )
        
        # Combine results
        return Response({
            'simulation': {
                'run_id': str(sim_run.id),
                'result_id': str(sim_result.id),
                **sim_result_data,
            },
            'insight': insight_json,
        })
    
    @action(detail=False, methods=['get'])
    def runs(self, request):
        """
        GET /api/market-insight-new/runs?limit=20
        
        Get history of simulation runs.
        """
        limit = int(request.query_params.get('limit', 20))
        vertical = request.query_params.get('vertical')
        region = request.query_params.get('region')
        
        runs_query = MarketSimRun.objects.all()
        if vertical:
            runs_query = runs_query.filter(vertical=vertical)
        if region:
            runs_query = runs_query.filter(region=region)
        
        runs = runs_query.order_by('-created_at')[:limit]
        
        runs_data = []
        for run in runs:
            runs_data.append({
                'run_id': str(run.id),
                'question': run.question,
                'vertical': run.vertical,
                'region': run.region,
                'scenario_params': run.scenario_params,
                'created_at': run.created_at.isoformat(),
                'has_result': run.results.exists(),
            })
        
        return Response({'runs': runs_data})
    
    @action(detail=False, methods=['post'])
    def scenario(self, request):
        """
        POST /api/market-insight/scenario
        
        Run "what-if" perturbations:
        {
            "vertical": "beauty",
            "perturbations": {
                "price_tier_shift": "super_premium",
                "channel_shift": "dtc_heavy",
                "claim_emphasis": "clean",
                "bundle_vs_single": "bundle"
            },
            "selected_markets": [...],
            "baseline_results": {...}
        }
        
        Returns diffs on impacted clusters/segments.
        """
        vertical = request.data.get('vertical', 'beauty')
        perturbations = request.data.get('perturbations', {})
        selected_markets = request.data.get('selected_markets', [])
        baseline_results = request.data.get('baseline_results', {})
        
        # Determine impacted clusters based on perturbations
        impacted_clusters = []
        
        if perturbations.get('price_tier_shift'):
            # Price tier shifts affect premium/super-premium clusters
            impacted_clusters.extend(['Skincare Premium', 'Makeup Premium', 'Fragrance Premium'])
            if perturbations['price_tier_shift'] in ['super_premium', 'ultra_luxury']:
                impacted_clusters.extend(['Skincare Super-Premium', 'Ultra-Luxury Brands'])
        
        if perturbations.get('channel_shift'):
            # Channel shifts affect channel-specific markets
            if 'dtc' in perturbations['channel_shift'].lower():
                impacted_clusters.extend(['DTC-Focused Markets', 'Indie Brands'])
            elif 'sephora' in perturbations['channel_shift'].lower():
                impacted_clusters.extend(['Sephora-Heavy Markets', 'Prestige Brands'])
        
        if perturbations.get('claim_emphasis'):
            claim = perturbations['claim_emphasis']
            if claim == 'clean':
                impacted_clusters.extend(['Clean Beauty Brands', 'Indie Skincare'])
            elif claim == 'clinical':
                impacted_clusters.extend(['Clinical Skincare', 'Performance Brands'])
            elif claim == 'luxury_heritage':
                impacted_clusters.extend(['Heritage Luxury', 'Ultra-Luxury Brands'])
        
        # Calculate expected outcomes based on perturbations
        market_share_change = 0.0
        price_sensitivity_impact = 0.0
        channel_mix_shift = 0.0
        
        if perturbations.get('price_tier_shift'):
            if perturbations['price_tier_shift'] == 'super_premium':
                market_share_change = 0.03  # Small positive from trade-up
                price_sensitivity_impact = -0.15  # Less price sensitive at higher tier
            elif perturbations['price_tier_shift'] == 'ultra_luxury':
                market_share_change = -0.02  # Smaller addressable market
                price_sensitivity_impact = -0.25
        
        if perturbations.get('channel_shift'):
            if 'dtc' in perturbations['channel_shift'].lower():
                channel_mix_shift = 0.20  # Shift toward DTC
                market_share_change += 0.02  # DTC can expand reach
            elif 'sephora' in perturbations['channel_shift'].lower():
                channel_mix_shift = 0.15
                market_share_change += 0.01
        
        if perturbations.get('claim_emphasis'):
            if perturbations['claim_emphasis'] == 'clean':
                market_share_change += 0.04  # Growing segment
            elif perturbations['claim_emphasis'] == 'clinical':
                market_share_change += 0.02
        
        if perturbations.get('bundle_vs_single') == 'bundle':
            market_share_change += 0.01  # Bundles increase AOV
        
        # Generate scenario-specific recommendations
        recommendations = []
        
        if perturbations.get('price_tier_shift'):
            tier = perturbations['price_tier_shift'].replace('_', ' ').title()
            recommendations.append(f"Monitor competitor response to {tier} tier shift")
            recommendations.append(f"Adjust pricing strategy to support {tier} positioning")
        
        if perturbations.get('channel_shift'):
            channel = perturbations['channel_shift'].replace('_', ' ').title()
            recommendations.append(f"Gradually shift channel mix toward {channel}")
            recommendations.append("Ensure supply chain can support new channel requirements")
        
        if perturbations.get('claim_emphasis'):
            claim = perturbations['claim_emphasis'].replace('_', ' ').title()
            recommendations.append(f"Test {claim} messaging with target segments")
            recommendations.append(f"Align product formulations with {claim} positioning")
        
        if perturbations.get('bundle_vs_single') == 'bundle':
            recommendations.append("Develop bundle strategy with complementary products")
            recommendations.append("Test bundle pricing and value perception")
        
        # Calculate diffs from baseline
        diffs = {
            'recommended_actions': {
                'changed': len(recommendations),
                'new': recommendations[:3],  # Top 3 new recommendations
            }
        }
        
        # Compare with baseline if provided
        if baseline_results and baseline_results.get('recommended_actions'):
            baseline_actions = []
            if baseline_results['recommended_actions'].get('now'):
                baseline_actions.extend(baseline_results['recommended_actions']['now'])
            if baseline_results['recommended_actions'].get('next'):
                baseline_actions.extend(baseline_results['recommended_actions']['next'])
            
            # Find new actions not in baseline
            new_actions = [r for r in recommendations if r not in baseline_actions]
            diffs['recommended_actions']['new'] = new_actions[:3]
        
        return Response({
            'scenario': perturbations,
            'impacted_clusters': list(set(impacted_clusters))[:5],  # Unique, limit to 5
            'expected_outcomes': {
                'market_share_change': round(market_share_change, 3),
                'price_sensitivity_impact': round(price_sensitivity_impact, 3),
                'channel_mix_shift': round(channel_mix_shift, 3),
            },
            'recommendations': recommendations,
            'diffs': diffs,
        })
    
    @action(detail=False, methods=['post'])
    def seed(self, request):
        """
        POST /api/market-insight/seed
        
        Seed data for a vertical.
        {
            "vertical": "beauty",
            "clear_existing": false
        }
        """
        vertical = request.data.get('vertical', 'beauty')
        clear_existing = request.data.get('clear_existing', False)
        
        try:
            result = seed_all(vertical=vertical, clear_existing=clear_existing)
            return Response({
                'success': True,
                'vertical': vertical,
                'counts': {
                    'brands': len(result['brands']),
                    'markets': len(result['markets']),
                    'products': len(result['products']),
                    'signals': len(result['signals']),
                    'events': len(result['events']),
                },
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def rebuild_manifold(self, request):
        """
        POST /api/market-insight/rebuild-manifold
        
        Rebuild manifold for a vertical/region.
        {
            "vertical": "beauty",
            "region": "US"
        }
        """
        vertical = request.data.get('vertical', 'beauty')
        region = request.data.get('region', 'US')
        
        try:
            builder = ManifoldBuilder(vertical=vertical, region=region)
            points = builder.build_manifold(force_rebuild=True)
            
            return Response({
                'success': True,
                'vertical': vertical,
                'region': region,
                'point_count': points.count(),
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
