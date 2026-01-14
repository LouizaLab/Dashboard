"""
Seed data generators for Market Insight feature.
Creates synthetic but realistic data for Beauty (prestige) and Food markets.
"""
import random
from datetime import datetime, timedelta
from django.utils import timezone
from .market_insight_models import (
    MarketDefinition, Brand, Product, MarketSignal, InnovationEvent
)


# Beauty Brands (Prestige/Luxury)
BEAUTY_BRANDS = [
    # Heritage Luxury
    {'name': 'Chanel', 'type': 'luxury', 'tags': ['heritage', 'luxury', 'fragrance']},
    {'name': 'Dior', 'type': 'luxury', 'tags': ['heritage', 'luxury', 'makeup']},
    {'name': 'YSL Beauty', 'type': 'luxury', 'tags': ['heritage', 'luxury', 'makeup']},
    {'name': 'Guerlain', 'type': 'luxury', 'tags': ['heritage', 'luxury', 'fragrance']},
    {'name': 'La Mer', 'type': 'luxury', 'tags': ['heritage', 'luxury', 'skincare']},
    {'name': 'Tom Ford Beauty', 'type': 'luxury', 'tags': ['heritage', 'luxury', 'fragrance']},
    
    # Prestige
    {'name': 'Estée Lauder', 'type': 'prestige', 'tags': ['heritage', 'prestige', 'skincare']},
    {'name': 'Lancôme', 'type': 'prestige', 'tags': ['heritage', 'prestige', 'makeup']},
    {'name': 'Clinique', 'type': 'prestige', 'tags': ['heritage', 'prestige', 'skincare']},
    {'name': 'Drunk Elephant', 'type': 'prestige', 'tags': ['clean', 'prestige', 'skincare']},
    {'name': 'Tatcha', 'type': 'prestige', 'tags': ['clean', 'prestige', 'skincare']},
    {'name': 'Glossier', 'type': 'prestige', 'tags': ['indie', 'prestige', 'makeup']},
    {'name': 'Fenty Beauty', 'type': 'prestige', 'tags': ['indie', 'prestige', 'makeup']},
    {'name': 'Rare Beauty', 'type': 'prestige', 'tags': ['indie', 'prestige', 'makeup']},
    
    # Clinical/Derm
    {'name': 'SkinCeuticals', 'type': 'prestige', 'tags': ['clinical', 'prestige', 'skincare']},
    {'name': 'La Roche-Posay', 'type': 'prestige', 'tags': ['clinical', 'prestige', 'skincare']},
    {'name': 'Dermalogica', 'type': 'prestige', 'tags': ['clinical', 'prestige', 'skincare']},
    {'name': 'The Ordinary', 'type': 'prestige', 'tags': ['clinical', 'indie', 'skincare']},
    {'name': 'Paula\'s Choice', 'type': 'prestige', 'tags': ['clinical', 'indie', 'skincare']},
    
    # Indie Gaining Traction
    {'name': 'Summer Fridays', 'type': 'prestige', 'tags': ['indie', 'clean', 'skincare']},
    {'name': 'Glow Recipe', 'type': 'prestige', 'tags': ['indie', 'clean', 'skincare']},
    {'name': 'Kosas', 'type': 'prestige', 'tags': ['indie', 'clean', 'makeup']},
    {'name': 'Ilia', 'type': 'prestige', 'tags': ['indie', 'clean', 'makeup']},
    {'name': 'Milk Makeup', 'type': 'prestige', 'tags': ['indie', 'clean', 'makeup']},
    {'name': 'Tower 28', 'type': 'prestige', 'tags': ['indie', 'clean', 'makeup']},
    {'name': 'Saie', 'type': 'prestige', 'tags': ['indie', 'clean', 'makeup']},
    {'name': 'Merit', 'type': 'prestige', 'tags': ['indie', 'clean', 'makeup']},
    {'name': 'Westman Atelier', 'type': 'luxury', 'tags': ['indie', 'luxury', 'makeup']},
    {'name': 'Violette FR', 'type': 'prestige', 'tags': ['indie', 'prestige', 'makeup']},
]


# Food Brands (Better-for-you snacks)
FOOD_BRANDS = [
    {'name': 'Rxbar', 'type': 'prestige', 'tags': ['functional', 'protein', 'clean']},
    {'name': 'Kind', 'type': 'prestige', 'tags': ['functional', 'nuts', 'clean']},
    {'name': 'Quest', 'type': 'prestige', 'tags': ['functional', 'protein', 'low-carb']},
    {'name': 'Clif Bar', 'type': 'prestige', 'tags': ['functional', 'energy', 'organic']},
    {'name': 'Larabar', 'type': 'prestige', 'tags': ['functional', 'fruit', 'clean']},
    {'name': 'Perfect Bar', 'type': 'prestige', 'tags': ['functional', 'protein', 'refrigerated']},
    {'name': 'ONE Bar', 'type': 'prestige', 'tags': ['functional', 'protein', 'low-carb']},
    {'name': 'Built Bar', 'type': 'prestige', 'tags': ['functional', 'protein', 'low-calorie']},
]


def generate_beauty_markets():
    """Generate MarketDefinition entries for US Prestige Beauty."""
    markets = []
    
    # Skincare markets
    skincare_categories = [
        {'cat': 'Serums', 'sub': 'Vitamin C', 'tier': 'premium'},
        {'cat': 'Serums', 'sub': 'Retinol', 'tier': 'premium'},
        {'cat': 'Serums', 'sub': 'Hyaluronic Acid', 'tier': 'premium'},
        {'cat': 'Moisturizers', 'sub': 'Face Creams', 'tier': 'premium'},
        {'cat': 'Moisturizers', 'sub': 'Face Creams', 'tier': 'super_premium'},
        {'cat': 'Moisturizers', 'sub': 'Face Creams', 'tier': 'ultra_luxury'},
        {'cat': 'Cleansers', 'sub': 'Face Wash', 'tier': 'premium'},
        {'cat': 'Eye Care', 'sub': 'Eye Creams', 'tier': 'premium'},
        {'cat': 'Eye Care', 'sub': 'Eye Serums', 'tier': 'super_premium'},
        {'cat': 'Sunscreen', 'sub': 'Face SPF', 'tier': 'premium'},
    ]
    
    for cat_info in skincare_categories:
        market = MarketDefinition.objects.create(
            name=f"US Prestige Skincare | {cat_info['cat']} | {cat_info['sub']} | {cat_info['tier'].replace('_', ' ').title()}",
            region='US',
            vertical='beauty',
            category='Skincare',
            sub_category=cat_info['sub'],
            price_tier=cat_info['tier'],
            channel_mix={'Sephora': random.randint(30, 60), 'Ulta': random.randint(10, 30), 'DTC': random.randint(20, 40)},
            tags=['prestige', 'skincare', cat_info['tier']],
        )
        markets.append(market)
    
    # Makeup markets
    makeup_categories = [
        {'cat': 'Foundation', 'sub': 'Liquid', 'tier': 'premium'},
        {'cat': 'Foundation', 'sub': 'Liquid', 'tier': 'super_premium'},
        {'cat': 'Lipstick', 'sub': 'Bullet', 'tier': 'premium'},
        {'cat': 'Lipstick', 'sub': 'Liquid', 'tier': 'premium'},
        {'cat': 'Eyeshadow', 'sub': 'Palettes', 'tier': 'premium'},
        {'cat': 'Mascara', 'sub': 'Volumizing', 'tier': 'premium'},
        {'cat': 'Blush', 'sub': 'Powder', 'tier': 'premium'},
        {'cat': 'Concealer', 'sub': 'Liquid', 'tier': 'premium'},
    ]
    
    for cat_info in makeup_categories:
        market = MarketDefinition.objects.create(
            name=f"US Prestige Makeup | {cat_info['cat']} | {cat_info['sub']} | {cat_info['tier'].replace('_', ' ').title()}",
            region='US',
            vertical='beauty',
            category='Makeup',
            sub_category=cat_info['sub'],
            price_tier=cat_info['tier'],
            channel_mix={'Sephora': random.randint(40, 70), 'Ulta': random.randint(15, 35), 'DTC': random.randint(10, 30)},
            tags=['prestige', 'makeup', cat_info['tier']],
        )
        markets.append(market)
    
    # Fragrance markets
    fragrance_categories = [
        {'cat': 'EDP', 'sub': 'Women', 'tier': 'premium'},
        {'cat': 'EDP', 'sub': 'Women', 'tier': 'super_premium'},
        {'cat': 'EDP', 'sub': 'Women', 'tier': 'ultra_luxury'},
        {'cat': 'EDT', 'sub': 'Unisex', 'tier': 'premium'},
        {'cat': 'EDP', 'sub': 'Men', 'tier': 'premium'},
    ]
    
    for cat_info in fragrance_categories:
        market = MarketDefinition.objects.create(
            name=f"US Prestige Fragrance | {cat_info['cat']} | {cat_info['sub']} | {cat_info['tier'].replace('_', ' ').title()}",
            region='US',
            vertical='beauty',
            category='Fragrance',
            sub_category=cat_info['sub'],
            price_tier=cat_info['tier'],
            channel_mix={'Sephora': random.randint(25, 50), 'Dept Store': random.randint(20, 40), 'DTC': random.randint(15, 35)},
            tags=['prestige', 'fragrance', cat_info['tier']],
        )
        markets.append(market)
    
    return markets


def generate_food_markets():
    """Generate MarketDefinition entries for Food (better-for-you snacks)."""
    markets = []
    
    food_categories = [
        {'cat': 'Bars', 'sub': 'Protein Bars', 'tier': 'premium'},
        {'cat': 'Bars', 'sub': 'Energy Bars', 'tier': 'premium'},
        {'cat': 'Bars', 'sub': 'Snack Bars', 'tier': 'premium'},
        {'cat': 'Functional Snacks', 'sub': 'Protein Snacks', 'tier': 'premium'},
        {'cat': 'Functional Snacks', 'sub': 'Gut Health', 'tier': 'premium'},
        {'cat': 'Light Meals', 'sub': 'Meal Replacements', 'tier': 'premium'},
    ]
    
    for cat_info in food_categories:
        market = MarketDefinition.objects.create(
            name=f"US Food | {cat_info['cat']} | {cat_info['sub']} | {cat_info['tier'].replace('_', ' ').title()}",
            region='US',
            vertical='food',
            category=cat_info['cat'],
            sub_category=cat_info['sub'],
            price_tier=cat_info['tier'],
            channel_mix={'Amazon': random.randint(30, 50), 'Grocery': random.randint(20, 40), 'DTC': random.randint(20, 40)},
            tags=['functional', 'better-for-you', cat_info['tier']],
        )
        markets.append(market)
    
    return markets


def seed_brands(vertical='beauty'):
    """Seed brands for a given vertical."""
    brand_data = BEAUTY_BRANDS if vertical == 'beauty' else FOOD_BRANDS
    brands = []
    
    for bd in brand_data:
        brand, created = Brand.objects.get_or_create(
            name=bd['name'],
            defaults={
                'brand_type': bd['type'],
                'positioning_tags': bd['tags'],
            }
        )
        brands.append(brand)
    
    return brands


def seed_products(brands, vertical='beauty'):
    """Generate synthetic products for brands."""
    products = []
    
    for brand in brands:
        if vertical == 'beauty':
            # Generate 2-5 products per brand
            num_products = random.randint(2, 5)
            categories = ['Skincare', 'Makeup', 'Fragrance']
            category = random.choice(categories)
            
            if category == 'Skincare':
                sub_cats = ['Serums', 'Moisturizers', 'Cleansers', 'Eye Care']
                formats = ['serum', 'cream', 'cleanser', 'eye cream']
                claims = ['hydration', 'barrier repair', 'anti-aging', 'brightening', 'acne-fighting']
            elif category == 'Makeup':
                sub_cats = ['Foundation', 'Lipstick', 'Eyeshadow', 'Mascara']
                formats = ['liquid', 'stick', 'powder', 'mascara']
                claims = ['long-wear', 'buildable', 'natural finish', 'full coverage']
            else:  # Fragrance
                sub_cats = ['EDP', 'EDT']
                formats = ['spray', 'mist']
                claims = ['long-lasting', 'unique scent', 'seasonal']
            
            for i in range(num_products):
                sub_cat = random.choice(sub_cats)
                format_type = random.choice(formats)
                price = random.uniform(25, 200) if category != 'Fragrance' else random.uniform(50, 300)
                
                if price < 50:
                    tier = 'premium'
                elif price < 100:
                    tier = 'super_premium'
                else:
                    tier = 'ultra_luxury'
                
                product = Product.objects.create(
                    brand=brand,
                    name=f"{brand.name} {sub_cat} {format_type.title()}",
                    category=category,
                    sub_category=sub_cat,
                    price=price,
                    price_tier=tier,
                    claims=random.sample(claims, k=random.randint(1, 3)),
                    format=format_type,
                    ingredients=random.sample(['niacinamide', 'retinol', 'peptides', 'vitamin C', 'hyaluronic acid'], k=random.randint(1, 3)),
                    launch_date=datetime.now().date() - timedelta(days=random.randint(0, 730)),
                    channel=random.choice(['Sephora', 'Ulta', 'DTC', 'Amazon']),
                    is_bundle=random.random() < 0.2,
                    is_kit=random.random() < 0.15,
                )
                products.append(product)
        
        else:  # Food
            num_products = random.randint(1, 3)
            categories = ['Bars', 'Functional Snacks']
            
            for i in range(num_products):
                category = random.choice(categories)
                if category == 'Bars':
                    sub_cat = random.choice(['Protein Bars', 'Energy Bars', 'Snack Bars'])
                    format_type = 'bar'
                    price = random.uniform(2, 5)
                else:
                    sub_cat = random.choice(['Protein Snacks', 'Gut Health'])
                    format_type = 'pack'
                    price = random.uniform(3, 7)
                
                product = Product.objects.create(
                    brand=brand,
                    name=f"{brand.name} {sub_cat}",
                    category=category,
                    sub_category=sub_cat,
                    price=price,
                    price_tier='premium',
                    claims=random.sample(['protein', 'fiber', 'low-sugar', 'organic', 'non-GMO'], k=random.randint(1, 3)),
                    format=format_type,
                    ingredients=random.sample(['protein', 'fiber', 'nuts', 'dates', 'chocolate'], k=random.randint(2, 4)),
                    launch_date=datetime.now().date() - timedelta(days=random.randint(0, 365)),
                    channel=random.choice(['Amazon', 'Grocery', 'DTC']),
                    is_bundle=random.random() < 0.3,
                    is_kit=False,
                )
                products.append(product)
    
    return products


def seed_market_signals(markets):
    """Generate time-series signals for markets."""
    signals = []
    start_date = datetime.now().date() - timedelta(days=365)
    
    for market in markets:
        # Generate monthly signals
        for month_offset in range(12):
            date = start_date + timedelta(days=30 * month_offset)
            
            signal = MarketSignal.objects.create(
                market=market,
                date=date,
                intent_index=random.uniform(0.3, 0.9),
                price_elasticity_proxy=random.uniform(-2.0, -0.5),
                trend_momentum=random.uniform(-0.2, 0.5),
                social_velocity=random.uniform(0.1, 1.0),
                search_share_proxy=random.uniform(0.05, 0.3),
                review_sentiment_proxy=random.uniform(0.4, 0.95),
                notes=f"Synthetic signal data for {market.name}",
                source='synthetic_demo',
            )
            signals.append(signal)
    
    return signals


def seed_innovation_events(markets, brands, products):
    """Generate innovation events (launches, campaigns, etc.)."""
    events = []
    start_date = datetime.now().date() - timedelta(days=180)
    
    # Generate 20-30 events
    for i in range(random.randint(20, 30)):
        market = random.choice(markets)
        brand = random.choice(brands) if brands else None
        product = random.choice(products) if products and random.random() < 0.7 else None
        
        event_type = random.choice(['launch', 'reformulation', 'campaign', 'collab', 'channel_play'])
        
        innovation_tags = []
        if event_type == 'launch':
            innovation_tags = random.sample(['new claim', 'new format', 'bundle'], k=random.randint(1, 2))
        elif event_type == 'campaign':
            innovation_tags = ['campaign', 'influencer']
        elif event_type == 'channel_play':
            innovation_tags = ['channel expansion', 'exclusive']
        
        date = start_date + timedelta(days=random.randint(0, 180))
        
        event = InnovationEvent.objects.create(
            market=market,
            date=date,
            brand=brand,
            product=product,
            event_type=event_type,
            innovation_tags=innovation_tags,
            description=f"{event_type.title()} event for {market.name}",
        )
        events.append(event)
    
    return events


def seed_all(vertical='beauty', clear_existing=False):
    """Seed all data for a vertical."""
    if clear_existing:
        MarketDefinition.objects.filter(vertical=vertical).delete()
        Brand.objects.all().delete()
        Product.objects.all().delete()
    
    # Seed brands
    brands = seed_brands(vertical)
    
    # Seed markets
    if vertical == 'beauty':
        markets = generate_beauty_markets()
    else:
        markets = generate_food_markets()
    
    # Seed products
    products = seed_products(brands, vertical)
    
    # Seed signals
    signals = seed_market_signals(markets)
    
    # Seed innovation events
    events = seed_innovation_events(markets, brands, products)
    
    # Update competitor sets
    for market in markets:
        # Assign 3-8 random brands as competitors
        competitor_brands = random.sample(brands, k=min(random.randint(3, 8), len(brands)))
        market.competitor_set = [str(b.id) for b in competitor_brands]
        market.save()
    
    return {
        'brands': brands,
        'markets': markets,
        'products': products,
        'signals': signals,
        'events': events,
    }
