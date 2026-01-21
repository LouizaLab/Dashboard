import { useState, useEffect } from 'react';
import { updateRecipeVariant, createRecipeVariant, deleteRecipeVariant } from '../../api';

function RecipeEditor({ variant, onVariantChange, onDelete, onCreateNew }) {
  const [editing, setEditing] = useState(!variant.id); // New variants start in edit mode
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    name: variant.name || '',
    base_product_id: variant.base_product_id || '',
    base_product_name: variant.base_product_name || '',
    nutrition_delta: variant.nutrition_delta_json || {
      calories: 0,
      sugar: 0,
      fat: 0,
      sodium: 0,
      protein: 0
    },
    sensory_delta: variant.sensory_delta_json || {
      sweetness: 0,
      saltiness: 0,
      texture: 0,
      heat: 0,
      aroma: 0
    },
    price_delta: variant.price_delta || 0,
    ingredient_changes: variant.ingredient_changes_json || {
      added: [],
      removed: [],
      substituted: {}
    },
    positioning_tags: variant.positioning_tags_json || [],
    description: variant.description || '',
  });

  useEffect(() => {
    // Reset form when variant changes
    setFormData({
      name: variant.name || '',
      base_product_id: variant.base_product_id || '',
      base_product_name: variant.base_product_name || '',
      nutrition_delta: variant.nutrition_delta_json || {
        calories: 0, sugar: 0, fat: 0, sodium: 0, protein: 0
      },
      sensory_delta: variant.sensory_delta_json || {
        sweetness: 0, saltiness: 0, texture: 0, heat: 0, aroma: 0
      },
      price_delta: variant.price_delta || 0,
      ingredient_changes: variant.ingredient_changes_json || {
        added: [], removed: [], substituted: {}
      },
      positioning_tags: variant.positioning_tags_json || [],
      description: variant.description || '',
    });
    setEditing(!variant.id);
  }, [variant.id]);

  const handleChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleNutritionChange = (key, value) => {
    handleChange('nutrition_delta', {
      ...formData.nutrition_delta,
      [key]: parseFloat(value) || 0
    });
  };

  const handleSensoryChange = (key, value) => {
    handleChange('sensory_delta', {
      ...formData.sensory_delta,
      [key]: parseFloat(value) || 0
    });
  };

  const handleIngredientAdd = (type, value) => {
    if (!value.trim()) return;

    const changes = { ...formData.ingredient_changes };
    if (type === 'added') {
      changes.added = [...(changes.added || []), value.trim()];
    } else if (type === 'removed') {
      changes.removed = [...(changes.removed || []), value.trim()];
    }
    handleChange('ingredient_changes', changes);
  };

  const handleIngredientSubstitute = (oldIng, newIng) => {
    if (!oldIng.trim() || !newIng.trim()) return;
    const changes = { ...formData.ingredient_changes };
    changes.substituted = { ...(changes.substituted || {}), [oldIng.trim()]: newIng.trim() };
    handleChange('ingredient_changes', changes);
  };

  const handleTagAdd = (tag) => {
    if (!tag.trim() || formData.positioning_tags.includes(tag.trim())) return;
    handleChange('positioning_tags', [...formData.positioning_tags, tag.trim()]);
  };

  const handleTagRemove = (tag) => {
    handleChange('positioning_tags', formData.positioning_tags.filter(t => t !== tag));
  };

  const handleSave = async () => {
    if (!formData.name.trim()) {
      alert('Please enter a name for the recipe variant');
      return;
    }

    setSaving(true);
    try {
      const payload = {
        name: formData.name,
        base_product_id: formData.base_product_id,
        base_product_name: formData.base_product_name,
        nutrition_delta_json: formData.nutrition_delta,
        sensory_delta_json: formData.sensory_delta,
        price_delta: formData.price_delta,
        ingredient_changes_json: formData.ingredient_changes,
        positioning_tags_json: formData.positioning_tags,
        description: formData.description,
      };

      let savedVariant;
      if (variant.id) {
        // Update existing
        const response = await updateRecipeVariant(variant.id, payload);
        savedVariant = response.data;
      } else {
        // Create new
        const response = await createRecipeVariant(payload);
        savedVariant = response.data;
        if (onCreateNew) onCreateNew(savedVariant);
      }

      onVariantChange(savedVariant);
      setEditing(false);
    } catch (error) {
      console.error('Failed to save recipe variant:', error);
      alert('Failed to save: ' + (error.response?.data?.error || error.message));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!variant.id) return;
    if (!confirm(`Are you sure you want to delete "${variant.name}"?`)) return;

    try {
      await deleteRecipeVariant(variant.id);
      if (onDelete) onDelete(variant.id);
    } catch (error) {
      console.error('Failed to delete recipe variant:', error);
      alert('Failed to delete: ' + (error.response?.data?.error || error.message));
    }
  };

  const handleCancel = () => {
    if (variant.id) {
      // Reset to original values
      setFormData({
        name: variant.name || '',
        base_product_id: variant.base_product_id || '',
        base_product_name: variant.base_product_name || '',
        nutrition_delta: variant.nutrition_delta_json || {},
        sensory_delta: variant.sensory_delta_json || {},
        price_delta: variant.price_delta || 0,
        ingredient_changes: variant.ingredient_changes_json || {},
        positioning_tags: variant.positioning_tags_json || [],
        description: variant.description || '',
      });
      setEditing(false);
    } else {
      // New variant - just reset
      setFormData({
        name: '',
        base_product_id: '',
        base_product_name: '',
        nutrition_delta: { calories: 0, sugar: 0, fat: 0, sodium: 0, protein: 0 },
        sensory_delta: { sweetness: 0, saltiness: 0, texture: 0, heat: 0, aroma: 0 },
        price_delta: 0,
        ingredient_changes: { added: [], removed: [], substituted: {} },
        positioning_tags: [],
        description: '',
      });
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">
          {variant.id ? 'Recipe Details' : 'New Recipe Variant'}
        </h3>
        <div className="flex gap-2">
          {variant.id && !editing && (
            <button
              onClick={handleDelete}
              className="px-3 py-1 text-sm bg-red-500/20 text-red-400 rounded hover:bg-red-500/30"
            >
              Delete
            </button>
          )}
          {editing ? (
            <>
              <button
                onClick={handleCancel}
                className="px-3 py-1 text-sm bg-gray-600/40 rounded hover:bg-gray-700/50 backdrop-blur-sm"
                disabled={saving}
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-3 py-1 text-sm bg-accent-primary rounded hover:bg-accent-primary/80 disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
            </>
          ) : (
            <button
              onClick={() => setEditing(true)}
              className="px-3 py-1 text-sm bg-accent-primary rounded hover:bg-accent-primary/80"
            >
              Edit
            </button>
          )}
        </div>
      </div>

      {editing ? (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Name *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              className="w-full px-3 py-2 bg-dark-surface border border-dark-border rounded text-white"
              placeholder="e.g., Low Sodium Burger"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Base Product ID</label>
            <input
              type="text"
              value={formData.base_product_id}
              onChange={(e) => handleChange('base_product_id', e.target.value)}
              className="w-full px-3 py-2 bg-dark-surface border border-dark-border rounded text-white"
              placeholder="e.g., burger_001"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Base Product Name</label>
            <input
              type="text"
              value={formData.base_product_name}
              onChange={(e) => handleChange('base_product_name', e.target.value)}
              className="w-full px-3 py-2 bg-dark-surface border border-dark-border rounded text-white"
              placeholder="e.g., Classic Burger"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Nutrition Changes (%)</label>
            <div className="space-y-2">
              {['calories', 'sugar', 'fat', 'sodium', 'protein'].map((nutrient) => (
                <div key={nutrient} className="flex items-center justify-between">
                  <span className="text-sm capitalize w-24">{nutrient}:</span>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.nutrition_delta[nutrient] || 0}
                    onChange={(e) => handleNutritionChange(nutrient, e.target.value)}
                    className="flex-1 px-2 py-1 bg-dark-surface border border-dark-border rounded text-white text-sm ml-2"
                  />
                  <span className="text-xs text-gray-400 ml-2">%</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Sensory Changes (-1 to +1)</label>
            <div className="space-y-2">
              {['sweetness', 'saltiness', 'texture', 'heat', 'aroma'].map((sensory) => (
                <div key={sensory} className="flex items-center gap-2">
                  <span className="text-sm capitalize w-24">{sensory}:</span>
                  <input
                    type="range"
                    min="-1"
                    max="1"
                    step="0.1"
                    value={formData.sensory_delta[sensory] || 0}
                    onChange={(e) => handleSensoryChange(sensory, e.target.value)}
                    className="flex-1"
                  />
                  <span className="text-xs w-12 text-right">
                    {formData.sensory_delta[sensory]?.toFixed(1) || '0.0'}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Price Change ($)</label>
            <input
              type="number"
              step="0.01"
              value={formData.price_delta}
              onChange={(e) => handleChange('price_delta', parseFloat(e.target.value) || 0)}
              className="w-full px-3 py-2 bg-dark-surface border border-dark-border rounded text-white"
              placeholder="0.00"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Positioning Tags</label>
            <div className="flex flex-wrap gap-2 mb-2">
              {formData.positioning_tags.map((tag, idx) => (
                <span
                  key={idx}
                  className="px-2 py-1 bg-accent-primary/20 text-accent-primary rounded text-xs flex items-center gap-1"
                >
                  {tag}
                  <button
                    onClick={() => handleTagRemove(tag)}
                    className="hover:text-red-400"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Add tag (e.g., healthy, premium)"
                className="flex-1 px-2 py-1 bg-dark-surface border border-dark-border rounded text-white text-sm"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleTagAdd(e.target.value);
                    e.target.value = '';
                  }
                }}
              />
              <button
                onClick={(e) => {
                  const input = e.target.previousElementSibling;
                  handleTagAdd(input.value);
                  input.value = '';
                }}
                className="px-3 py-1 bg-dark-surface border border-dark-border rounded text-sm hover:bg-dark-hover"
              >
                Add
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => handleChange('description', e.target.value)}
              className="w-full px-3 py-2 bg-dark-surface border border-dark-border rounded text-white text-sm"
              rows="3"
              placeholder="Describe the recipe changes..."
            />
          </div>
        </div>
      ) : (
        <div className="space-y-3 text-sm">
          {formData.description && (
            <div>
              <div className="text-gray-400 mb-1">Description:</div>
              <div className="pl-2 text-gray-300">{formData.description}</div>
            </div>
          )}
          <div>
            <div className="text-gray-400 mb-1">Nutrition Changes:</div>
            <div className="pl-2">
              {Object.entries(formData.nutrition_delta).map(([key, value]) => (
                value !== 0 && (
                  <div key={key} className="flex justify-between">
                    <span className="capitalize">{key}:</span>
                    <span className={value >= 0 ? 'text-green-400' : 'text-red-400'}>
                      {value >= 0 ? '+' : ''}{value.toFixed(1)}%
                    </span>
                  </div>
                )
              ))}
            </div>
          </div>
          <div>
            <div className="text-gray-400 mb-1">Price Change:</div>
            <div className={`pl-2 ${formData.price_delta >= 0 ? 'text-red-400' : 'text-green-400'}`}>
              ${formData.price_delta >= 0 ? '+' : ''}{formData.price_delta.toFixed(2)}
            </div>
          </div>
          {formData.positioning_tags && formData.positioning_tags.length > 0 && (
            <div>
              <div className="text-gray-400 mb-1">Positioning:</div>
              <div className="flex flex-wrap gap-1 pl-2">
                {formData.positioning_tags.map((tag, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-1 bg-dark-surface rounded text-xs"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default RecipeEditor;
