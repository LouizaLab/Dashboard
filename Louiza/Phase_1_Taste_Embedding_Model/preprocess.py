"""
Data preprocessing pipeline for Phase 1: Taste Embedding Model
Normalizes multiple datasets into a canonical schema
"""

import pandas as pd
import numpy as np
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')


# Canonical schema fields
CANONICAL_FIELDS = [
    'product_id',
    'product_name',
    'brand',
    'category',
    'subcategory',
    'ingredients',
    'sensory_tags',
    'nutrition_json',
    'description',
    'price',
    'source_dataset'
]

# Common sensory tags mapping
SENSORY_TAG_MAPPING = {
    'sweet': ['sweet', 'sugar', 'honey', 'syrup', 'caramel', 'chocolate', 'vanilla'],
    'bitter': ['bitter', 'coffee', 'dark chocolate', 'tea'],
    'salty': ['salt', 'salted', 'sodium'],
    'sour': ['sour', 'lemon', 'lime', 'vinegar', 'citrus'],
    'spicy': ['spicy', 'hot', 'pepper', 'chili', 'jalapeno', 'harberno', 'chipotle'],
    'creamy': ['creamy', 'cream', 'cheese', 'butter', 'mayo', 'ranch'],
    'fizzy': ['fizzy', 'carbonated', 'soda', 'cola', 'sprite'],
    'fried': ['fried', 'crispy', 'breaded'],
    'grilled': ['grilled', 'flame-grilled'],
    'smoky': ['smoky', 'smoke', 'barbeque', 'bbq']
}


def extract_sensory_tags(text: str, ingredients: str = "") -> List[str]:
    """
    Extract sensory tags from product name, description, and ingredients
    """
    if pd.isna(text):
        text = ""
    if pd.isna(ingredients):
        ingredients = ""
    
    combined_text = (str(text) + " " + str(ingredients)).lower()
    tags = []
    
    for tag, keywords in SENSORY_TAG_MAPPING.items():
        if any(keyword in combined_text for keyword in keywords):
            tags.append(tag)
    
    return tags


def normalize_nutrition(row: pd.Series, source: str) -> Dict:
    """
    Normalize nutrition data from different sources into standard format
    """
    nutrition = {}
    
    if source == 'mcd':
        nutrition = {
            'calories': float(row.get('energy', 0)) if pd.notna(row.get('energy')) else 0,
            'sugar_g': float(row.get('total_sugar', 0)) if pd.notna(row.get('total_sugar')) else 0,
            'fat_g': float(row.get('total_fat', 0)) if pd.notna(row.get('total_fat')) else 0,
            'protein_g': float(row.get('protein', 0)) if pd.notna(row.get('protein')) else 0,
            'sodium_mg': float(row.get('sodium', 0)) if pd.notna(row.get('sodium')) else 0,
            'caffeine_mg': 0  # Not available in this dataset
        }
    elif source in ['burger-king', 'wendys']:
        nutrition = {
            'calories': float(row.get('Calories', 0)) if pd.notna(row.get('Calories')) else 0,
            'sugar_g': float(row.get('Sugars (g)', 0)) if pd.notna(row.get('Sugars (g)')) else 0,
            'fat_g': float(row.get('Fat (g)', 0)) if pd.notna(row.get('Fat (g)')) else 0,
            'protein_g': float(row.get('Protein (g)', 0)) if pd.notna(row.get('Protein (g)')) else 0,
            'sodium_mg': float(row.get('Sodium (mg)', 0)) if pd.notna(row.get('Sodium (mg)')) else 0,
            'caffeine_mg': 0  # Estimate based on category
        }
        
        # Estimate caffeine for coffee/tea/energy drinks
        category = str(row.get('Category', '')).lower()
        if 'coffee' in category or 'coffee' in str(row.get('Item', '')).lower():
            nutrition['caffeine_mg'] = 95  # Average coffee
        elif 'tea' in category or 'tea' in str(row.get('Item', '')).lower():
            nutrition['caffeine_mg'] = 40  # Average tea
        elif 'cola' in str(row.get('Item', '')).lower() or 'coke' in str(row.get('Item', '')).lower():
            nutrition['caffeine_mg'] = 34  # Average cola
    else:
        nutrition = {
            'calories': 0,
            'sugar_g': 0,
            'fat_g': 0,
            'protein_g': 0,
            'sodium_mg': 0,
            'caffeine_mg': 0
        }
    
    return nutrition


def clean_ingredients(ingredients: str) -> str:
    """
    Clean and normalize ingredient strings
    """
    if pd.isna(ingredients) or ingredients == '':
        return ''
    
    # Remove extra whitespace, normalize separators
    ingredients = str(ingredients).strip()
    ingredients = re.sub(r'\s+', ' ', ingredients)
    ingredients = re.sub(r'[,;]\s*', ', ', ingredients)
    
    return ingredients


def process_mcd_dataset(file_path: Path) -> pd.DataFrame:
    """
    Process McDonald's dataset (mcd.csv)
    """
    df = pd.read_csv(file_path)
    records = []
    
    for idx, row in df.iterrows():
        product_name = str(row.get('name', 'Unknown'))
        
        # Extract category from name or use default
        category = 'Food'
        if any(x in product_name.lower() for x in ['coffee', 'tea', 'drink', 'float']):
            category = 'Beverage'
        elif any(x in product_name.lower() for x in ['burger', 'sandwich']):
            category = 'Burger'
        elif any(x in product_name.lower() for x in ['nugget', 'chicken']):
            category = 'Chicken'
        elif 'fries' in product_name.lower():
            category = 'Side'
        
        ingredients = clean_ingredients(row.get('ingredients', ''))
        description = str(row.get('description', '')) if pd.notna(row.get('description')) else ''
        
        sensory_tags = extract_sensory_tags(product_name + " " + description, ingredients)
        nutrition = normalize_nutrition(row, 'mcd')
        
        records.append({
            'product_id': f"mcd_{idx}",
            'product_name': product_name,
            'brand': 'McDonald\'s',
            'category': category,
            'subcategory': row.get('tag', ''),
            'ingredients': ingredients,
            'sensory_tags': ', '.join(sensory_tags) if sensory_tags else '',
            'nutrition_json': json.dumps(nutrition),
            'description': description,
            'price': None,
            'source_dataset': 'mcd'
        })
    
    return pd.DataFrame(records)


def process_burger_king_dataset(file_path: Path) -> pd.DataFrame:
    """
    Process Burger King menu dataset
    """
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding='latin-1')
    records = []
    
    for idx, row in df.iterrows():
        product_name = str(row.get('Item', 'Unknown'))
        category = str(row.get('Category', 'Unknown'))
        
        # Infer ingredients from name and category
        ingredients = product_name  # Use name as proxy for ingredients
        description = f"{product_name} from {category} category"
        
        sensory_tags = extract_sensory_tags(product_name + " " + category, '')
        nutrition = normalize_nutrition(row, 'burger-king')
        
        records.append({
            'product_id': f"bk_{idx}",
            'product_name': product_name,
            'brand': 'Burger King',
            'category': category,
            'subcategory': '',
            'ingredients': ingredients,
            'sensory_tags': ', '.join(sensory_tags) if sensory_tags else '',
            'nutrition_json': json.dumps(nutrition),
            'description': description,
            'price': None,
            'source_dataset': 'burger-king'
        })
    
    return pd.DataFrame(records)


def process_wendys_dataset(file_path: Path) -> pd.DataFrame:
    """
    Process Wendy's menu dataset
    """
    df = pd.read_csv(file_path)
    records = []
    
    for idx, row in df.iterrows():
        product_name = str(row.get('Item', 'Unknown'))
        category = str(row.get('Category', 'Unknown'))
        
        # Infer ingredients from name and category
        ingredients = product_name
        description = f"{product_name} from {category} category"
        
        sensory_tags = extract_sensory_tags(product_name + " " + category, '')
        nutrition = normalize_nutrition(row, 'wendys')
        
        records.append({
            'product_id': f"wendys_{idx}",
            'product_name': product_name,
            'brand': 'Wendy\'s',
            'category': category,
            'subcategory': '',
            'ingredients': ingredients,
            'sensory_tags': ', '.join(sensory_tags) if sensory_tags else '',
            'nutrition_json': json.dumps(nutrition),
            'description': description,
            'price': None,
            'source_dataset': 'wendys'
        })
    
    return pd.DataFrame(records)


def main():
    """
    Main preprocessing pipeline
    """
    data_dir = Path(__file__).parent / 'data'
    raw_dir = data_dir / 'raw'
    processed_dir = data_dir / 'processed'
    processed_dir.mkdir(exist_ok=True)
    
    print("Starting data preprocessing pipeline...")
    print(f"Raw data directory: {raw_dir}")
    print(f"Processed data directory: {processed_dir}")
    
    all_dataframes = []
    
    # Process each dataset
    datasets = {
        'mcd.csv': process_mcd_dataset,
        'burger-king-menu.csv': process_burger_king_dataset,
        'wendys-menu.csv': process_wendys_dataset
    }
    
    for filename, processor in datasets.items():
        file_path = raw_dir / filename
        if file_path.exists():
            print(f"\nProcessing {filename}...")
            try:
                df = processor(file_path)
                all_dataframes.append(df)
                print(f"  Processed {len(df)} products")
            except Exception as e:
                print(f"  Error processing {filename}: {e}")
        else:
            print(f"  File not found: {filename}")
    
    if not all_dataframes:
        print("\nNo datasets processed. Please check data/raw directory.")
        return
    
    # Combine all datasets
    print("\nCombining all datasets...")
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    
    # Ensure all canonical fields are present
    for field in CANONICAL_FIELDS:
        if field not in combined_df.columns:
            combined_df[field] = None
    
    # Reorder columns
    combined_df = combined_df[CANONICAL_FIELDS]
    
    # Save processed data
    output_file = processed_dir / 'products.csv'
    combined_df.to_csv(output_file, index=False)
    
    print(f"\n✓ Preprocessing complete!")
    print(f"  Total products: {len(combined_df)}")
    print(f"  Output file: {output_file}")
    print(f"\nDataset breakdown:")
    print(combined_df['source_dataset'].value_counts())
    print(f"\nCategory breakdown:")
    print(combined_df['category'].value_counts())
    
    # Save summary statistics
    summary = {
        'total_products': int(len(combined_df)),
        'datasets': {k: int(v) for k, v in combined_df['source_dataset'].value_counts().to_dict().items()},
        'categories': {k: int(v) for k, v in combined_df['category'].value_counts().to_dict().items()},
        'products_with_ingredients': int(combined_df['ingredients'].notna().sum()),
        'products_with_tags': int((combined_df['sensory_tags'] != '').sum()),
        'products_with_description': int(combined_df['description'].notna().sum())
    }
    
    summary_file = processed_dir / 'summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✓ Summary saved to: {summary_file}")


if __name__ == '__main__':
    main()

