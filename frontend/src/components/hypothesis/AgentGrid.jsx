import { useState, useEffect } from 'react';

const archetypeColors = {
  'value_seeker': '#f59e0b',      // orange
  'health_optimizer': '#3b82f6',  // blue
  'convenience_loyalist': '#10b981', // green
  'late_night_craver': '#8b5cf6',   // purple
  'trend_chaser': '#ec4899',        // pink
  'family_bundle_buyer': '#06b6d4', // cyan
  'protein_maximizer': '#ef4444',   // red
};

function AgentGrid({ agents, onAgentClick, selectedAgentIds = [], onClearSelection }) {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredAgents = agents.filter(agent => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      agent.display_name?.toLowerCase().includes(query) ||
      agent.archetype_display?.toLowerCase().includes(query) ||
      agent.region?.toLowerCase().includes(query) ||
      agent.age_bucket?.toLowerCase().includes(query)
    );
  });

  const getAgentColor = (archetype) => {
    return archetypeColors[archetype] || '#6b7280';
  };

  const getInitials = (name) => {
    if (!name) return '?';
    const parts = name.split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  return (
    <div className="flex flex-col h-full">
      {/* Search Bar */}
      <div className="mb-6">
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search agents by name, archetype, or region..."
            className="w-full bg-dark-surface border border-dark-border rounded-xl px-4 py-3 pr-10 text-gray-100 placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:ring-accent-primary/50 focus:border-accent-primary"
          />
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>
        <div className="mt-2 text-xs text-gray-400">
          Showing {filteredAgents.length} of {agents.length} agents
        </div>
      </div>

      {/* Agent Grid */}
      <div className="flex-1 overflow-y-auto">
        {/* Group agents by archetype for better visualization */}
        {(() => {
          const groupedAgents = {};
          filteredAgents.forEach(agent => {
            const archetype = agent.archetype || 'other';
            if (!groupedAgents[archetype]) {
              groupedAgents[archetype] = [];
            }
            groupedAgents[archetype].push(agent);
          });

          return Object.entries(groupedAgents).map(([archetype, archetypeAgents]) => (
            <div key={archetype} className="mb-8">
              <div className="flex items-center gap-3 mb-4">
                <div
                  className="w-1 h-6 rounded-full"
                  style={{ backgroundColor: getAgentColor(archetype) }}
                />
                <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
                  {archetypeAgents[0]?.archetype_display || archetype} ({archetypeAgents.length})
                </h3>
              </div>
              <div className="grid grid-cols-6 gap-4">
                {archetypeAgents.map((agent) => {
                  const color = getAgentColor(agent.archetype);
                  const isSelected = selectedAgentIds.includes(agent.id);
                  
                  return (
                    <button
                      key={agent.id}
                      onClick={() => onAgentClick(agent.id)}
                      className={`flex flex-col items-center p-4 rounded-xl transition-all hover:scale-105 ${
                        isSelected
                          ? 'bg-dark-surface border-2 shadow-lg'
                          : 'bg-dark-hover border border-dark-border hover:border-accent-primary/50'
                      }`}
                      style={{
                        borderColor: isSelected ? color : undefined,
                        boxShadow: isSelected ? `0 0 20px ${color}40` : undefined,
                      }}
                    >
                      {/* Agent Avatar */}
                      <div
                        className="w-16 h-16 rounded-full flex items-center justify-center text-white font-bold text-lg mb-2 relative"
                        style={{
                          backgroundColor: color,
                          boxShadow: `0 4px 12px ${color}60`,
                        }}
                      >
                        {getInitials(agent.display_name)}
                        {isSelected && (
                          <div
                            className="absolute -top-1 -right-1 w-5 h-5 rounded-full border-2 border-dark-bg flex items-center justify-center"
                            style={{ backgroundColor: color }}
                          >
                            <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          </div>
                        )}
                      </div>
                      
                      {/* Agent Name */}
                      <div className="text-sm font-medium text-gray-200 text-center mb-1">
                        {agent.display_name}
                      </div>
                      
                      {/* Archetype Badge */}
                      <div
                        className="text-xs px-2 py-1 rounded-full text-white font-medium"
                        style={{ backgroundColor: color }}
                      >
                        {agent.archetype_display}
                      </div>
                      
                      {/* Quick Info */}
                      <div className="mt-2 text-xs text-gray-400 text-center">
                        <div>{agent.age_bucket} • {agent.region}</div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          ));
        })()}
        
        {filteredAgents.length === 0 && (
          <div className="flex items-center justify-center h-64 text-gray-400">
            <div className="text-center">
              <div className="text-lg mb-2">No agents found</div>
              <div className="text-sm">Try adjusting your search or filters</div>
            </div>
          </div>
        )}
      </div>
      
      {/* Selected Agents Summary */}
      {selectedAgentIds.length > 0 && (
        <div className="mt-4 pt-4 border-t border-dark-border">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-400">
              <span className="font-semibold text-accent-primary">{selectedAgentIds.length}</span> agent{selectedAgentIds.length !== 1 ? 's' : ''} selected for simulation
            </div>
            {onClearSelection && (
              <button
                onClick={onClearSelection}
                className="text-xs text-gray-400 hover:text-gray-200 transition-colors"
              >
                Clear Selection
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default AgentGrid;

