import { useState } from 'react';

const simulationTypes = [
  { id: 'survey', label: 'Survey', icon: '📋' },
  { id: 'article', label: 'Article', icon: '📰' },
  { id: 'website', label: 'Website Content', icon: '🌐' },
  { id: 'ad', label: 'Ad', icon: '📢' },
  { id: 'linkedin', label: 'LinkedIn Post', icon: '💼' },
  { id: 'instagram', label: 'Instagram Post', icon: '📸' },
  { id: 'twitter', label: 'X Post', icon: '🐦' },
];

function SimulationPanel() {
  const [scenario, setScenario] = useState(null);
  const [showToast, setShowToast] = useState(false);

  const handleSimulationClick = (type) => {
    setScenario(type);
    setShowToast(true);
    setTimeout(() => setShowToast(false), 3000);
  };

  return (
    <>
      <div className="bg-dark-surface border-t border-dark-border p-4">
        <div className="max-w-6xl mx-auto">
          <h3 className="text-sm font-semibold text-gray-300 mb-3">
            WHAT WOULD YOU LIKE TO SIMULATE?
          </h3>
          <div className="flex flex-wrap gap-2">
            {simulationTypes.map((type) => (
              <button
                key={type.id}
                onClick={() => handleSimulationClick(type.id)}
                className="px-4 py-2 bg-dark-hover border border-dark-border rounded-lg text-sm font-medium text-gray-300 hover:bg-accent-primary hover:text-white hover:border-accent-primary transition-all flex items-center gap-2"
              >
                <span>{type.icon}</span>
                <span>{type.label}</span>
              </button>
            ))}
          </div>
          {scenario && (
            <div className="mt-3 text-xs text-gray-400">
              Active scenario: <span className="text-accent-primary font-semibold">{scenario}</span>
            </div>
          )}
        </div>
      </div>

      {showToast && (
        <div className="fixed bottom-4 right-4 bg-accent-primary text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-fade-in">
          <div className="flex items-center gap-2">
            <span>✓</span>
            <span>Simulation scenario activated: {scenario}</span>
          </div>
        </div>
      )}
    </>
  );
}

export default SimulationPanel;

