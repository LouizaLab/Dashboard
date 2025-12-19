import { useState, useEffect } from 'react';
import ChatPanel from './ChatPanel';
import SurveyPanel from './SurveyPanel';
import TasteTestPanel from './TasteTestPanel';

function AgentDrawer({ isOpen, onClose, agent, filters }) {
  const [activeTab, setActiveTab] = useState('profile');
  const [agentData, setAgentData] = useState(null);

  useEffect(() => {
    if (!isOpen) {
      setAgentData(null);
      return;
    }
    
    if (agent) {
      // Always set agentData immediately to show data right away
      console.log('Setting agentData from agent prop:', agent);
      setAgentData(agent);
      
      // If agent has id but might be missing some fields, try to fetch full data
      // But don't wait for it - show what we have immediately
      if (agent.id && (!agent.archetype || !agent.biography)) {
        console.log('Agent might be missing fields, fetching full data in background');
        loadAgentData();
      }
    }
  }, [agent?.id, isOpen]);

  const loadAgentData = async () => {
    if (!agent) {
      console.warn('Cannot load agent data: agent is missing');
      return;
    }
    
    if (!agent.id) {
      console.warn('Agent missing id, using agent directly:', agent);
      setAgentData(agent);
      return;
    }
    
    try {
      console.log('Fetching agent data for ID:', agent.id);
      const response = await fetch(`http://localhost:8000/api/agents/${agent.id}/`);
      
      if (!response.ok) {
        if (response.status === 404) {
          console.warn(`Agent ${agent.id} not found (404), using provided agent data`);
          // Use the agent prop directly if API returns 404
          setAgentData(agent);
          return;
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Successfully loaded agent data:', data);
      
      // Ensure id is set
      if (!data.id) {
        data.id = agent.id;
      }
      
      setAgentData(data);
    } catch (error) {
      console.error('Failed to load agent:', error);
      // Set agentData to agent as fallback if API fails
      if (agent) {
        console.log('Using agent as fallback:', agent);
        setAgentData(agent);
      }
    }
  };

  if (!isOpen || !agent) return null;

  const tabs = [
    { id: 'profile', label: 'Profile' },
    { id: 'chat', label: 'Chat' },
    { id: 'survey', label: 'Survey' },
    { id: 'taste_test', label: 'Taste Test' },
  ];

  const getArchetypeColor = (archetype) => {
    const colors = {
      'value_seeker': '#f59e0b',
      'health_optimizer': '#3b82f6',
      'convenience_loyalist': '#10b981',
      'late_night_craver': '#8b5cf6',
      'trend_chaser': '#ec4899',
      'family_bundle_buyer': '#06b6d4',
      'protein_maximizer': '#ef4444',
    };
    return colors[archetype] || '#6b7280';
  };

  const getInitials = (name) => {
    if (!name) return '?';
    const parts = name.split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  const agentColor = agentData ? getArchetypeColor(agentData.archetype) : '#6b7280';

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-dark-surface border-l border-dark-border shadow-2xl z-50 flex flex-col">
      <div className="p-5 border-b border-dark-border bg-dark-surface/95 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            {(agentData || agent) && (() => {
              const displayAgent = agentData || agent;
              const archetype = displayAgent.archetype || displayAgent.archetype_display;
              const color = archetype ? getArchetypeColor(archetype) : '#6b7280';
              return (
                <div
                  className="w-12 h-12 rounded-full flex items-center justify-center text-white font-bold text-lg"
                  style={{
                    backgroundColor: color,
                    boxShadow: `0 4px 12px ${color}60`,
                  }}
                >
                  {getInitials(displayAgent.display_name)}
                </div>
              );
            })()}
            <div>
              <h2 className="text-lg font-bold text-gray-100">{(agentData || agent)?.display_name || 'Agent'}</h2>
              {(agentData || agent)?.archetype_display && (
                <div className="text-xs text-gray-400 mt-1">{(agentData || agent).archetype_display}</div>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-xl w-8 h-8 flex items-center justify-center rounded hover:bg-dark-hover transition-colors"
          >
            ×
          </button>
        </div>
        <div className="flex space-x-1 bg-dark-hover rounded-lg p-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 px-3 py-1.5 rounded text-xs font-medium transition-all ${
                activeTab === tab.id
                  ? 'bg-accent-primary text-white shadow-lg'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'profile' && (agentData || agent) && (() => {
          const profileAgent = agentData || agent;
          return (
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-semibold text-gray-400 mb-2">Archetype</h3>
                <div className="bg-dark-hover rounded p-2 text-sm">
                  {profileAgent.archetype_display || profileAgent.archetype || 'N/A'}
                </div>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-400 mb-2">Demographics</h3>
                <div className="bg-dark-hover rounded p-2 text-sm space-y-1">
                  <div>Age: {profileAgent.age_bucket || 'N/A'}</div>
                  <div>Gender: {profileAgent.gender || 'N/A'}</div>
                  <div>Region: {profileAgent.region || 'N/A'}</div>
                  <div>Income: {profileAgent.income || 'N/A'}</div>
                </div>
              </div>
              {(profileAgent.taste_profile_json && profileAgent.taste_profile_json.length > 0) && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-400 mb-2">Taste Profile</h3>
                  <div className="flex flex-wrap gap-2">
                    {profileAgent.taste_profile_json.map((tag, idx) => (
                      <span
                        key={idx}
                        className="bg-accent-primary/20 text-accent-primary rounded px-2 py-1 text-xs"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {profileAgent.biography && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-400 mb-2">Biography</h3>
                  <p className="text-sm text-gray-300">{profileAgent.biography}</p>
                </div>
              )}
            </div>
          );
        })()}

        {activeTab === 'chat' && (() => {
          const chatAgent = agentData || agent;
          
          // If we have agent but no agentData yet, and agent has id, we're loading
          const isLoading = agent && agent.id && !agentData && isOpen;
          
          if (isLoading) {
            return (
              <div className="flex items-center justify-center h-full text-gray-400">
                <div className="text-center">
                  <div className="text-sm mb-2">Loading agent data...</div>
                  <div className="text-xs">Please wait</div>
                </div>
              </div>
            );
          }
          
          if (!chatAgent) {
            return (
              <div className="flex items-center justify-center h-full text-gray-400">
                <div className="text-center">
                  <div className="text-sm mb-2">No agent selected</div>
                  <div className="text-xs">Please select an agent from the grid</div>
                </div>
              </div>
            );
          }
          
          if (!chatAgent.id) {
            console.error('ChatAgent missing ID:', chatAgent);
            return (
              <div className="flex items-center justify-center h-full text-gray-400">
                <div className="text-center">
                  <div className="text-sm mb-2">Agent data incomplete</div>
                  <div className="text-xs">Please try selecting the agent again</div>
                </div>
              </div>
            );
          }
          
          return (
            <ChatPanel 
              agent={chatAgent} 
              filters={filters}
              key={chatAgent.id}
            />
          );
        })()}

        {activeTab === 'survey' && (
          <SurveyPanel agent={agent} filters={filters} />
        )}

        {activeTab === 'taste_test' && (
          <TasteTestPanel agent={agent} filters={filters} />
        )}
      </div>
    </div>
  );
}

export default AgentDrawer;

