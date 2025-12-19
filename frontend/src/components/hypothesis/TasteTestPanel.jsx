import { useState } from 'react';

function TasteTestPanel({ agent, filters }) {
  const [items, setItems] = useState(['McDonald\'s', 'Burger King', 'Chipotle', 'Taco Bell']);
  const [inputItem, setInputItem] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAddItem = () => {
    if (inputItem.trim() && !items.includes(inputItem.trim())) {
      setItems([...items, inputItem.trim()]);
      setInputItem('');
    }
  };

  const handleRemoveItem = (item) => {
    setItems(items.filter((i) => i !== item));
  };

  const handleRunTasteTest = async () => {
    if (items.length === 0) return;

    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/taste_test/run/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agent_id: agent?.id || null,
          filters: {
            age_bucket: filters.age_bucket || null,
            gender: filters.gender || null,
            region: filters.region || null,
            income: filters.income || null,
            archetype: filters.archetype || null,
          },
          agent_count: filters.agent_count,
          items: items,
          mode: filters.use_gpt ? 'gpt' : 'mock',
        }),
      });

      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Taste test error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-gray-400 mb-2">Test Items</h3>
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={inputItem}
            onChange={(e) => setInputItem(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleAddItem()}
            placeholder="Add item..."
            className="flex-1 bg-dark-hover border border-dark-border rounded px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-accent-primary"
          />
          <button
            onClick={handleAddItem}
            className="bg-accent-primary text-white rounded px-4 py-2 text-sm"
          >
            Add
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {items.map((item, idx) => (
            <div
              key={idx}
              className="bg-dark-hover border border-dark-border rounded px-3 py-1 text-sm flex items-center gap-2"
            >
              <span className="text-gray-300">{item}</span>
              <button
                onClick={() => handleRemoveItem(item)}
                className="text-gray-500 hover:text-red-400"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      </div>

      <button
        onClick={handleRunTasteTest}
        disabled={items.length === 0 || loading}
        className="w-full bg-accent-primary text-white rounded px-4 py-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? 'Running Taste Test...' : 'Run Taste Test'}
      </button>

      {results && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-gray-400">Rankings</h3>
          <div className="space-y-2">
            {results.rankings?.map((ranking, idx) => (
              <div
                key={idx}
                className="bg-dark-hover border border-dark-border rounded p-3"
              >
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm font-medium text-gray-200">
                    #{idx + 1} {ranking.item}
                  </span>
                  <span className="text-xs text-accent-primary">
                    {(ranking.average_score * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="flex-1 bg-dark-bg rounded-full h-2">
                  <div
                    className="h-2 rounded-full bg-accent-primary"
                    style={{ width: `${ranking.average_score * 100}%` }}
                  />
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {ranking.response_count} responses
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default TasteTestPanel;

