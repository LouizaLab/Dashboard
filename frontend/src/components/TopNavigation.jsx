const tabs = [
  'TEST HYPOTHESIS',
  'NETWORK GRAPH',
  'TASTE SNAPSHOT',
  'BEHAVIORAL DYNAMICS',
  'INSIGHTS',
  'WHAT-IF SIMULATION',
];

function TopNavigation({ activeTab, setActiveTab }) {
  return (
    <div className="bg-dark-surface border-b border-dark-border px-6 py-3">
      <div className="flex space-x-1">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === tab
                ? 'bg-accent-primary text-white shadow-lg shadow-accent-primary/50'
                : 'text-gray-400 hover:text-gray-200 hover:bg-dark-hover'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>
    </div>
  );
}

export default TopNavigation;

