"""
Evidence Retriever for Agent-Tron

Retrieves persona-specific, LPM-grounded evidence from Data Engine.
Each persona gets different amounts and types of evidence based on their characteristics.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

# Add Data_Engine to path
current_file = Path(__file__).resolve()
# agent_tron/core/evidence_retriever.py -> agent_tron/core -> agent_tron -> project root
project_root = current_file.parent.parent.parent
data_engine_parent = project_root  # Data_Engine is at project root level

# Add project root to path so we can import Data_Engine
if str(data_engine_parent) not in sys.path:
    sys.path.insert(0, str(data_engine_parent))

try:
    from Data_Engine.data_engine import DataEngine
    from Data_Engine.core.schema import DataRecord
    DATA_ENGINE_AVAILABLE = True
    logger.info(f"✓ Data Engine imported successfully from {data_engine_parent}")
except ImportError as e:
    logger.warning(f"Data Engine not available: {e}")
    logger.warning(f"Tried importing from: {data_engine_parent}")
    logger.warning(f"Python path: {sys.path[:3]}")
    DATA_ENGINE_AVAILABLE = False
    DataEngine = None
    DataRecord = None

# Try to import sentence transformers for embeddings
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None


class EvidenceRetriever:
    """
    Retrieves persona-specific evidence from Data Engine.
    
    Features:
    - Persona-specific evidence amounts/types
    - LPM-grounded retrieval (uses LPM outputs to guide search)
    - Real survey/interview evidence from Data Engine
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize evidence retriever.
        
        Args:
            storage_dir: Data Engine storage directory. Defaults to Data_Engine/storage_data
        """
        print(f"[EvidenceRetriever] Initializing... DATA_ENGINE_AVAILABLE: {DATA_ENGINE_AVAILABLE}")
        if not DATA_ENGINE_AVAILABLE:
            logger.warning("Data Engine not available. Evidence retrieval will be disabled.")
            print("[EvidenceRetriever] ❌ Data Engine not available - import failed")
            self.data_engine = None
            self.embedding_model = None
            return
        
        # Set up storage directory
        if storage_dir is None:
            storage_dir = project_root / "Data_Engine" / "storage_data"
        
        self.storage_dir = Path(storage_dir)
        print(f"[EvidenceRetriever] Storage dir: {self.storage_dir}")
        print(f"[EvidenceRetriever] Storage dir exists: {self.storage_dir.exists()}")
        logger.info(f"Initializing Evidence Retriever with storage_dir: {self.storage_dir}")
        logger.info(f"Storage dir exists: {self.storage_dir.exists()}")
        
        # Initialize Data Engine
        try:
            if not DATA_ENGINE_AVAILABLE:
                logger.error("Data Engine module not available - cannot initialize evidence retriever")
                print("[EvidenceRetriever] ❌ Data Engine module not available")
                self.data_engine = None
                self.embedding_model = None
                return
            
            print(f"[EvidenceRetriever] Initializing DataEngine with storage_dir={self.storage_dir}, embedding_dim=384")
            self.data_engine = DataEngine(storage_dir=self.storage_dir, embedding_dim=384)
            logger.info(f"✓ Data Engine initialized successfully")
            print(f"[EvidenceRetriever] ✓ Data Engine initialized successfully")
            
            # Set up embedding function if available
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                try:
                    logger.info("Loading sentence transformer model...")
                    self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                    self.data_engine.set_embedding_fn(self.embedding_model.encode)
                    logger.info("✓ Evidence retriever initialized with sentence transformers")
                except Exception as e:
                    logger.warning(f"Failed to load sentence transformer: {e}", exc_info=True)
                    self.embedding_model = None
            else:
                self.embedding_model = None
                logger.warning("Sentence transformers not available. Semantic search disabled.")
            
            # Test if we can actually query the data
            try:
                print(f"[EvidenceRetriever] Testing Data Engine query (bucket_id=2)...")
                test_records = self.data_engine.get_by_bucket(bucket_id=2, limit=1)
                logger.info(f"✓ Data Engine test query successful - found {len(test_records)} test records")
                print(f"[EvidenceRetriever] ✓ Test query successful - found {len(test_records)} records")
            except Exception as e:
                logger.warning(f"Data Engine test query failed: {e}", exc_info=True)
                print(f"[EvidenceRetriever] ⚠️ Test query failed: {e}")
                import traceback
                traceback.print_exc()
            
        except Exception as e:
            logger.error(f"Failed to initialize Data Engine: {e}", exc_info=True)
            print(f"[EvidenceRetriever] ❌ Failed to initialize Data Engine: {e}")
            import traceback
            traceback.print_exc()
            self.data_engine = None
            self.embedding_model = None
    
    def _get_evidence_count_for_persona(self, persona: Dict[str, Any]) -> int:
        """
        Determine how many evidence items to retrieve for a persona.
        
        Different personas get different amounts based on their archetype and characteristics.
        
        Args:
            persona: Persona dict with archetype, demographics, psychographics
        
        Returns:
            Number of evidence items to retrieve
        """
        archetype = persona.get('archetype', 'unknown')
        psychographics = persona.get('psychographics', {})
        
        # Base counts by archetype
        archetype_counts = {
            'value_seeker': 15,  # Value seekers want more evidence
            'health_optimizer': 12,
            'convenience_loyalist': 10,
            'late_night_craver': 8,
            'trend_chaser': 12,
            'family_bundle_buyer': 10,
            'protein_maximizer': 10,
        }
        
        base_count = archetype_counts.get(archetype, 10)
        
        # Adjust based on psychographics
        novelty_seeking = psychographics.get('novelty_seeking', 0.5)
        if novelty_seeking > 0.7:
            # High novelty seekers want more diverse evidence
            base_count += 3
        
        brand_loyalty = psychographics.get('brand_loyalty', 0.5)
        if brand_loyalty < 0.3:
            # Low brand loyalty - want more comparison evidence
            base_count += 2
        
        return min(base_count, 20)  # Cap at 20
    
    def _build_persona_query(self, persona: Dict[str, Any], hypothesis: str, lpm_outputs: Dict[str, Any]) -> str:
        """
        Build a query string based on persona and LPM outputs.
        
        Args:
            persona: Persona dict
            hypothesis: Hypothesis/question
            lpm_outputs: LPM outputs including sampled_decision and conditioned_distribution
        
        Returns:
            Query string for Data Engine
        """
        archetype = persona.get('archetype', '')
        demographics = persona.get('demographics', {})
        psychographics = persona.get('psychographics', {})
        
        # Get LPM decision to ground the query
        sampled_decision = lpm_outputs.get('sampled_decision', {})
        choice = sampled_decision.get('choice', '')
        
        # Build query components
        query_parts = [hypothesis]
        
        # Add persona-specific keywords
        archetype_keywords = {
            'value_seeker': 'price value deal discount affordable',
            'health_optimizer': 'healthy nutrition calories ingredients',
            'convenience_loyalist': 'quick fast convenient easy',
            'late_night_craver': 'late night snack craving',
            'trend_chaser': 'popular trending new latest',
            'family_bundle_buyer': 'family kids bundle meal',
            'protein_maximizer': 'protein meat filling satisfying',
        }
        
        if archetype in archetype_keywords:
            query_parts.append(archetype_keywords[archetype])
        
        # Add demographic context
        age_bucket = demographics.get('age_bucket', '')
        if age_bucket:
            query_parts.append(age_bucket)
        
        region = demographics.get('region', '')
        if region:
            query_parts.append(region)
        
        # Add LPM-grounded preference
        if choice:
            query_parts.append(choice)
        
        # Add psychographic emphasis
        if psychographics.get('price_sensitivity', 0) > 0.7:
            query_parts.append('price cost money')
        if psychographics.get('health_consciousness', 0) > 0.7:
            query_parts.append('health healthy')
        
        return ' '.join(query_parts)
    
    def _build_persona_filters(self, persona: Dict[str, Any], lpm_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build filters for Data Engine query based on persona and LPM outputs.
        
        Args:
            persona: Persona dict
            lpm_outputs: LPM outputs
        
        Returns:
            Filter dict for Data Engine
        """
        filters = {}
        
        # Filter by bucket (prioritize surveys/interviews - bucket 2)
        filters['bucket_id'] = 2  # Survey/interview data
        
        # Filter by demographics if available in data
        demographics = persona.get('demographics', {})
        region = demographics.get('region', '')
        if region:
            # Map region to data engine format if needed
            filters['categorical_fields.region'] = region
        
        # Note: Brand filtering is now done in retrieve_evidence using hypothesis extraction
        # LPM product IDs don't map directly to brands, so we extract from hypothesis instead
        
        return filters
    
    def _record_to_evidence_item(self, record: DataRecord, index: int, brands_from_hypothesis: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        Convert DataRecord to EvidenceItem format.
        
        Args:
            record: DataRecord from Data Engine
            index: Index for unique evidence_id
        
        Returns:
            EvidenceItem dict
        """
        # Extract text content
        text_content = record.get_text_for_embedding() or ''
        
        # If no text, try structured fields
        if not text_content and record.structured_fields:
            # Try common text fields
            for field in ['response', 'answer', 'comment', 'text', 'content', 'quote', 'transcript']:
                if field in record.structured_fields:
                    text_content = str(record.structured_fields[field])
                    break
        
        # If still no text, use raw_text
        if not text_content and record.raw_text:
            text_content = record.raw_text
        
        # Truncate if too long
        excerpt = text_content[:500] if len(text_content) > 500 else text_content
        
        # Skip if no content
        if not excerpt or len(excerpt.strip()) < 10:
            logger.debug(f"Skipping record {record.record_id} - no text content")
            return None
        
        # Extract metadata
        source_name = record.source_name or 'unknown'
        brand = record.brand or ''
        
        # Try to extract brand from text if not in metadata
        if not brand and brands_from_hypothesis:
            text_lower = text_content.lower()
            for b in brands_from_hypothesis:
                if b.lower() in text_lower:
                    brand = b
                    break
        
        # Build evidence item
        evidence_item = {
            'evidence_id': f"de_{record.record_id}_{index}",
            'source_type': f"survey_interview_{source_name}",
            'title': f"Survey/Interview Response",
            'date': str(record.timestamp) if record.timestamp else None,
            'region': record.categorical_fields.get('region') if record.categorical_fields else None,
            'sample_size': 1,  # Each record is one response
            'excerpt': excerpt,
            'tags': [],
            'weight': float(record.sentiment) if record.sentiment is not None else 0.5
        }
        
        # Add tags based on content
        if brand:
            evidence_item['tags'].append(brand.lower())
        
        # Add archetype tags if available
        if record.categorical_fields:
            archetype = record.categorical_fields.get('archetype')
            if archetype:
                evidence_item['tags'].append(archetype)
        
        return evidence_item
    
    def _extract_brands_from_hypothesis(self, hypothesis: str) -> List[str]:
        """
        Extract brand names from hypothesis text.
        
        Args:
            hypothesis: Hypothesis/question text
        
        Returns:
            List of brand names found
        """
        hypothesis_lower = hypothesis.lower()
        brands = []
        
        if 'mcdonalds' in hypothesis_lower or "mcdonald's" in hypothesis_lower:
            brands.append("McDonald's")
        if 'burger king' in hypothesis_lower or 'bk' in hypothesis_lower:
            brands.append('Burger King')
        if 'wendys' in hypothesis_lower or "wendy's" in hypothesis_lower:
            brands.append("Wendy's")
        if 'chipotle' in hypothesis_lower:
            brands.append('Chipotle')
        if 'starbucks' in hypothesis_lower:
            brands.append('Starbucks')
        
        return brands
    
    def retrieve_evidence(
        self,
        persona: Dict[str, Any],
        hypothesis: str,
        lpm_outputs: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve persona-specific, LPM-grounded evidence from Data Engine.
        
        Args:
            persona: Persona dict with archetype, demographics, psychographics
            hypothesis: Hypothesis/question
            lpm_outputs: LPM outputs including sampled_decision, conditioned_distribution
            context: Optional context dict
        
        Returns:
            List of EvidenceItem dicts
        """
        if not self.data_engine:
            logger.warning(f"Data Engine not available for agent {persona.get('archetype', 'unknown')}. Returning empty evidence.")
            return []
        
        logger.info(f"Starting evidence retrieval for persona {persona.get('archetype', 'unknown')}, hypothesis: {hypothesis[:100]}")
        
        try:
            # Determine evidence count for this persona
            evidence_count = self._get_evidence_count_for_persona(persona)
            
            # Extract brands from hypothesis (more reliable than LPM product IDs)
            brands_from_hypothesis = self._extract_brands_from_hypothesis(hypothesis)
            
            # Build query and filters
            query = self._build_persona_query(persona, hypothesis, lpm_outputs)
            
            # Build filters - prioritize surveys/interviews
            filters = {'bucket_id': 2}  # Survey/interview data
            
            persona_id = persona.get('agent_id', 'unknown')
            sampled_decision = lpm_outputs.get('sampled_decision', {})
            sampled_choice = sampled_decision.get('choice', 'N/A')
            sampled_prob = sampled_decision.get('probability', 0.0)
            logger.info(
                f"Retrieving {evidence_count} evidence items for persona {persona.get('archetype', 'unknown')} "
                f"(ID: {persona_id[:8]}...) with query: {query[:100]}... brands: {brands_from_hypothesis}, "
                f"LPM sampled: {sampled_choice} (prob: {sampled_prob:.3f})"
            )
            print(f"[EvidenceRetriever] Persona {persona.get('archetype', 'unknown')} (ID: {persona_id[:8]}...): Retrieving {evidence_count} items")
            print(f"[EvidenceRetriever] LPM sampled decision: {sampled_choice} (prob: {sampled_prob:.3f})")
            
            # Retrieve evidence
            evidence_items = []
            
            # Strategy 1: Semantic search (PRIMARY METHOD)
            # Brand metadata may not be set, so use semantic search with brand keywords
            if self.embedding_model and self.data_engine.embedding_fn:
                try:
                    # Enhance query with brand names from hypothesis
                    enhanced_query = query
                    if brands_from_hypothesis:
                        enhanced_query = f"{query} {' '.join(brands_from_hypothesis)}"
                    
                    logger.info(f"Trying semantic search with query: {enhanced_query[:150]}")
                    
                    records = self.data_engine.search(
                        query=enhanced_query,
                        filters=filters,
                        top_k=evidence_count * 3  # Get more for filtering
                    )
                    
                    logger.info(f"Semantic search returned {len(records)} records")
                    
                    # Filter records that mention brands from hypothesis (if brands specified)
                    if brands_from_hypothesis and records:
                        filtered_records = []
                        for record in records:
                            text = record.get_text_for_embedding().lower()
                            if any(brand.lower() in text for brand in brands_from_hypothesis):
                                filtered_records.append(record)
                        if filtered_records:
                            records = filtered_records[:evidence_count * 2]
                            logger.info(f"Filtered to {len(filtered_records)} records mentioning brands")
                        else:
                            # If no brand matches, use all records (they're still relevant)
                            logger.info("No brand matches found, using all semantic search results")
                    
                    # Convert to evidence items
                    existing_ids = set()
                    for idx, record in enumerate(records):
                        if len(evidence_items) >= evidence_count:
                            break
                        evidence_item = self._record_to_evidence_item(record, len(evidence_items), brands_from_hypothesis)
                        if evidence_item and evidence_item['evidence_id'] not in existing_ids:
                            evidence_items.append(evidence_item)
                            existing_ids.add(evidence_item['evidence_id'])
                    
                    logger.info(f"Added {len(evidence_items)} items via semantic search")
                    
                except Exception as e:
                    logger.warning(f"Semantic search failed: {e}. Trying fallback methods.", exc_info=True)
            
            # Strategy 2: Persona-specific bucket-based retrieval (surveys/interviews)
            # This ensures we always get some evidence even without embeddings
            if len(evidence_items) < evidence_count:
                try:
                    logger.info(f"Trying persona-specific bucket retrieval for bucket 2 (need {evidence_count - len(evidence_items)} more items)")
                    
                    # Get more records to filter from (persona-specific)
                    # Use persona ID to get different starting point for different personas
                    import hashlib
                    persona_id = persona.get('agent_id', 'unknown')
                    seed = int(hashlib.md5(persona_id.encode()).hexdigest()[:8], 16) % 10000
                    
                    # Get larger set to allow for persona-specific selection
                    # Different personas get different limits to vary the pool
                    limit_multiplier = 15 + (seed % 10)  # Vary between 15-24
                    bucket_records = self.data_engine.get_by_bucket(bucket_id=2, limit=evidence_count * limit_multiplier)
                    logger.info(f"Bucket retrieval returned {len(bucket_records)} records for persona {persona.get('archetype', 'unknown')}")
                    print(f"[EvidenceRetriever] Persona {persona.get('archetype', 'unknown')}: Got {len(bucket_records)} records, seed: {seed}")
                    
                    # Persona-specific filtering
                    filtered_records = []
                    archetype = persona.get('archetype', '')
                    demographics = persona.get('demographics', {})
                    psychographics = persona.get('psychographics', {})
                    
                    # Build persona keywords for text matching
                    persona_keywords = []
                    archetype_keywords_map = {
                        'value_seeker': ['price', 'value', 'deal', 'discount', 'affordable', 'cheap', 'cost'],
                        'health_optimizer': ['healthy', 'nutrition', 'calories', 'ingredients', 'fresh', 'organic'],
                        'convenience_loyalist': ['quick', 'fast', 'convenient', 'easy', 'drive-thru', 'speed'],
                        'late_night_craver': ['late', 'night', 'snack', 'craving', 'midnight', 'after hours'],
                        'trend_chaser': ['popular', 'trending', 'new', 'latest', 'viral', 'buzz'],
                        'family_bundle_buyer': ['family', 'kids', 'bundle', 'meal', 'sharing', 'group'],
                        'protein_maximizer': ['protein', 'meat', 'filling', 'satisfying', 'hearty', 'substantial'],
                    }
                    if archetype in archetype_keywords_map:
                        persona_keywords.extend(archetype_keywords_map[archetype])
                    
                    # Add psychographic keywords
                    if psychographics.get('price_sensitivity', 0) > 0.7:
                        persona_keywords.extend(['price', 'cost', 'money', 'budget'])
                    if psychographics.get('health_consciousness', 0) > 0.7:
                        persona_keywords.extend(['healthy', 'nutrition', 'calories'])
                    if psychographics.get('novelty_seeking', 0) > 0.7:
                        persona_keywords.extend(['new', 'different', 'try', 'unique'])
                    
                    # Score and filter records based on persona match
                    scored_records = []
                    for record in bucket_records:
                        text = record.get_text_for_embedding().lower()
                        score = 0
                        
                        # Brand matching (required if brands specified)
                        brand_match = True
                        if brands_from_hypothesis:
                            brand_match = any(brand.lower() in text for brand in brands_from_hypothesis)
                            if brand_match:
                                score += 10  # High priority for brand matches
                        
                        if not brand_match and brands_from_hypothesis:
                            continue  # Skip if brands specified but not found
                        
                        # Persona keyword matching (weighted by archetype relevance)
                        keyword_matches = sum(1 for kw in persona_keywords if kw.lower() in text)
                        score += keyword_matches * 3  # Increased weight for persona keywords
                        
                        # Bonus for multiple persona keyword matches (stronger persona alignment)
                        if keyword_matches >= 2:
                            score += 3
                        if keyword_matches >= 3:
                            score += 2
                        
                        # Demographic matching (if available in record)
                        if record.categorical_fields:
                            record_archetype = record.categorical_fields.get('archetype', '')
                            if record_archetype == archetype:
                                score += 5
                            
                            record_region = record.categorical_fields.get('region', '')
                            if record_region and demographics.get('region'):
                                if record_region.lower() == demographics.get('region', '').lower():
                                    score += 3
                        
                        # Age bucket matching (if available)
                        if demographics.get('age_bucket'):
                            age_keywords = demographics.get('age_bucket', '').lower().split('-')
                            if any(age_kw in text for age_kw in age_keywords):
                                score += 2
                        
                        scored_records.append((score, record))
                    
                    if not scored_records:
                        logger.warning(f"No scored records for persona {archetype}, skipping to next strategy")
                    else:
                        top_score = max(score for score, _ in scored_records)
                        print(f"[EvidenceRetriever] Persona {archetype}: Scored {len(scored_records)} records, top score: {top_score}, keywords: {persona_keywords[:5]}")
                        logger.info(f"Persona {archetype}: Top scoring record has score {top_score}, persona keywords: {persona_keywords[:5]}")
                        
                        # Sort by score (highest first) and take top matches
                        scored_records.sort(key=lambda x: x[0], reverse=True)
                        
                        # Use persona-specific randomization for tie-breaking
                        # This ensures different personas get different evidence even with same scores
                        import random
                        random.seed(seed)
                        
                        # Group by score and shuffle within each score group
                        from collections import defaultdict
                        score_groups = defaultdict(list)
                        for score, record in scored_records:
                            score_groups[score].append(record)
                        
                        # Shuffle each score group deterministically based on persona
                        shuffled_records = []
                        for score in sorted(score_groups.keys(), reverse=True):
                            group = score_groups[score]
                            random.shuffle(group)  # Deterministic shuffle based on seed
                            shuffled_records.extend(group)
                        
                        bucket_records = shuffled_records[:evidence_count * 3]
                        
                        print(f"[EvidenceRetriever] Persona {archetype}: Filtered to {len(bucket_records)} records (persona-shuffled)")
                        logger.info(f"Persona-filtered to {len(bucket_records)} records (top scores, persona-shuffled)")
                        
                        # Add new records
                        existing_ids = {item['evidence_id'] for item in evidence_items}
                        added_count = 0
                        for idx, record in enumerate(bucket_records):
                            if len(evidence_items) >= evidence_count:
                                break
                            evidence_item = self._record_to_evidence_item(record, len(evidence_items), brands_from_hypothesis)
                            if evidence_item and evidence_item['evidence_id'] not in existing_ids:
                                evidence_items.append(evidence_item)
                                existing_ids.add(evidence_item['evidence_id'])
                                added_count += 1
                        
                        # Log evidence IDs for this persona
                        evidence_ids = [item['evidence_id'] for item in evidence_items[-added_count:]]
                        all_evidence_ids = [item['evidence_id'] for item in evidence_items]
                        print(f"[EvidenceRetriever] Persona {archetype} (ID: {persona_id[:8]}...): Added {added_count} items")
                        print(f"[EvidenceRetriever] Persona {archetype}: Total {len(evidence_items)} evidence IDs: {[eid[:16] + '...' for eid in all_evidence_ids[:5]]}")
                        logger.info(f"Added {len(evidence_items)} total items via persona-specific bucket retrieval")
                        logger.info(f"Persona {archetype} (ID: {persona_id[:8]}...): All evidence IDs ({len(all_evidence_ids)}): {[eid[:32] for eid in all_evidence_ids]}")
                except Exception as e:
                    logger.warning(f"Bucket retrieval failed: {e}", exc_info=True)
            
            # Strategy 3: Final fallback with persona-based randomization
            if len(evidence_items) < evidence_count:
                try:
                    logger.info(f"Final fallback: persona-randomized bucket retrieval")
                    # Use persona agent_id as seed for deterministic but varied results
                    import hashlib
                    persona_id = persona.get('agent_id', 'unknown')
                    seed = int(hashlib.md5(persona_id.encode()).hexdigest()[:8], 16) % 10000
                    
                    # Get larger set and shuffle deterministically based on persona
                    bucket_records = self.data_engine.get_by_bucket(bucket_id=2, limit=evidence_count * 5)
                    logger.info(f"Bucket retrieval returned {len(bucket_records)} records")
                    
                    # Deterministic shuffle based on persona
                    import random
                    random.seed(seed)
                    shuffled = list(bucket_records)
                    random.shuffle(shuffled)
                    bucket_records = shuffled
                    
                    # Filter by brand mentions if brands specified
                    if brands_from_hypothesis:
                        filtered_records = []
                        for record in bucket_records:
                            text = record.get_text_for_embedding().lower()
                            if any(brand.lower() in text for brand in brands_from_hypothesis):
                                filtered_records.append(record)
                        if filtered_records:
                            bucket_records = filtered_records
                            logger.info(f"Filtered to {len(filtered_records)} records mentioning brands")
                    
                    # Add new records
                    existing_ids = {item['evidence_id'] for item in evidence_items}
                    for idx, record in enumerate(bucket_records):
                        if len(evidence_items) >= evidence_count:
                            break
                        evidence_item = self._record_to_evidence_item(record, len(evidence_items), brands_from_hypothesis)
                        if evidence_item and evidence_item['evidence_id'] not in existing_ids:
                            evidence_items.append(evidence_item)
                            existing_ids.add(evidence_item['evidence_id'])
                    
                    logger.info(f"Added {len(evidence_items)} items via persona-randomized bucket retrieval")
                except Exception as e:
                    logger.warning(f"Final fallback retrieval failed: {e}")
            
            # Final summary log with all evidence IDs
            all_evidence_ids = [item['evidence_id'] for item in evidence_items]
            persona_id = persona.get('agent_id', 'unknown')
            archetype = persona.get('archetype', 'unknown')
            logger.info(
                f"✓ Retrieved {len(evidence_items)} evidence items for persona {archetype} (ID: {persona_id[:8]}...)"
            )
            logger.info(
                f"Persona {archetype} (ID: {persona_id[:8]}...): Final evidence IDs ({len(all_evidence_ids)}): "
                f"{[eid[:24] + '...' for eid in all_evidence_ids[:10]]}"
            )
            print(f"[EvidenceRetriever] ✓ Persona {archetype}: Final {len(evidence_items)} evidence items")
            if all_evidence_ids:
                print(f"[EvidenceRetriever] Evidence IDs (first 5): {[eid[:20] + '...' for eid in all_evidence_ids[:5]]}")
            
            return evidence_items
            
        except Exception as e:
            logger.error(f"Failed to retrieve evidence: {e}", exc_info=True)
            import traceback
            logger.error(traceback.format_exc())
            return []

