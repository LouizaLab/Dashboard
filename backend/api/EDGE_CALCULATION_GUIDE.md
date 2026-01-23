# Edge Weight Calculation Guide

## Overview

The network graph edge weights are now calculated using **actual company metrics** instead of random values. This ensures accurate and official data representation.

## How It Works

### Calculation Methods

The `EdgeWeightCalculator` class computes edge weights using statistical methods:

1. **Intent Overlap**: Cosine similarity of `intent_index` time series
2. **Taste Similarity**: Cosine similarity of `taste_index` time series  
3. **Foot Traffic Correlation**: Pearson correlation of `foot_traffic` time series
4. **Revenue Correlation**: Pearson correlation of `revenue` time series
5. **Substitution Likelihood**: Weighted combination of intent and taste similarity
6. **Co-visit Probability**: Based on foot traffic correlation
7. **Brand Adjacency**: Combined similarity metric

### Overall Weight Formula

The overall edge weight is calculated as a weighted average:

```
weight = 0.30 × intent_overlap
       + 0.25 × taste_similarity
       + 0.15 × foot_traffic_correlation
       + 0.15 × revenue_correlation
       + 0.15 × brand_adjacency
```

All values are normalized to the range [0, 1].

## Usage

### Recalculate All Edges

To recalculate all edges based on current metrics:

```bash
python manage.py recalculate_edges
```

Options:
- `--lookback-days N`: Number of days to look back (default: 90)
- `--min-data-points N`: Minimum data points required (default: 10)
- `--dry-run`: Show what would be calculated without saving

Example:
```bash
# Dry run to see what would change
python manage.py recalculate_edges --dry-run

# Recalculate with 120 days of data
python manage.py recalculate_edges --lookback-days 120

# Recalculate with stricter data requirements
python manage.py recalculate_edges --min-data-points 20
```

### Programmatic Usage

```python
from api.edge_calculator import EdgeWeightCalculator
from api.models import Company, Edge

# Initialize calculator
calculator = EdgeWeightCalculator(lookback_days=90, min_data_points=10)

# Calculate weight for two companies
company_a = Company.objects.get(name="McDonald's")
company_b = Company.objects.get(name="Burger King")

weight, factors, matrix = calculator.compute_edge_weight(company_a, company_b)

print(f"Overall weight: {weight:.3f}")
print(f"Intent overlap: {factors['intent_overlap']:.3f}")
print(f"Taste similarity: {factors['taste_similarity']:.3f}")

# Recalculate an existing edge
edge = Edge.objects.get(source_company=company_a, target_company=company_b)
edge.recalculate(lookback_days=90)
```

## Data Requirements

### Minimum Data Points

For accurate calculations, each company needs:
- At least 10 data points (configurable) for each metric
- Data spanning the lookback period (default: 90 days)

### Metrics Used

The calculator uses these metrics from `CompanyMetricPoint`:
- `intent_index`: Intent index values over time
- `taste_index`: Taste index values over time
- `foot_traffic`: Foot traffic values over time
- `revenue`: Revenue values over time

## Validation

The calculator includes validation:
- Checks for sufficient data points
- Handles missing dates gracefully
- Normalizes all values to [0, 1] range
- Returns 0.0 for insufficient data (instead of errors)

## Edge Factors

Each edge stores detailed factors in `factors_json`:

```json
{
  "intent_overlap": 0.75,
  "taste_similarity": 0.68,
  "foot_traffic_correlation": 0.82,
  "revenue_correlation": 0.71,
  "substitution_likelihood": 0.72,
  "co_visit_probability": 0.82,
  "brand_adjacency": 0.73
}
```

## Matrix Representation

Each edge also includes a 3×3 matrix in `matrix_json`:

- **Row 0**: Combined metrics (overlaps/correlations)
- **Row 1**: Source company metrics (normalized)
- **Row 2**: Target company metrics (normalized)

Columns represent: [Intent, Taste, Revenue]

## Best Practices

1. **Regular Recalculation**: Recalculate edges periodically as new metric data arrives
2. **Consistent Lookback**: Use the same lookback period for consistency
3. **Data Quality**: Ensure sufficient data points before recalculation
4. **Dry Run First**: Always use `--dry-run` first to preview changes

## Troubleshooting

### Edges with Zero Weight

If an edge has weight 0.0, it means:
- Insufficient data points for one or both companies
- No overlapping dates in the time series
- All calculated factors are zero

**Solution**: Ensure both companies have sufficient metric data.

### Inconsistent Results

If results seem inconsistent:
- Check data quality (missing dates, outliers)
- Verify lookback period covers sufficient data
- Increase `min_data_points` for stricter requirements

### Performance

For large datasets:
- Recalculation processes edges sequentially
- Consider running during off-peak hours
- Use `--dry-run` to estimate processing time

## API Integration

The network graph API (`/api/network/`) automatically uses the calculated edge weights. The view type determines which factor is used:

- **Market Insight**: Overall weight
- **Foot Traffic**: `foot_traffic_correlation`
- **Revenue**: `revenue_correlation`
- **Intent**: `intent_overlap`
- **Taste Dynamics**: `taste_similarity`
