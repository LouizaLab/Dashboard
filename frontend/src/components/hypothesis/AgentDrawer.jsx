import { useState, useEffect } from 'react';
import ChatPanel from './ChatPanel';
import SurveyPanel from './SurveyPanel';
import TasteTestPanel from './TasteTestPanel';

function AgentDrawer({ isOpen, onClose, agent, filters }) {
  const [activeTab, setActiveTab] = useState('profile');
  const [agentData, setAgentData] = useState(null);

  useEffect(() => {
    if (agent && isOpen) {
      loadAgentData();
    }
  }, [agent, isOpen]);

  const loadAgentData = async () => {
    if (!agent) return;
    try {
      const response = await fetch(`http://localhost:8000/api/agents/${agent.id}/`);
      const data = await response.json();
      setAgentData(data);
    } catch (error) {
      console.error('Failed to load agent:', error);
    }
  };

  if (!isOpen || !agent) return null;

  const tabs = [
    { id: 'profile', label: 'Profile' },
    { id: 'chat', label: 'Chat' },
    { id: 'survey', label: 'Survey' },
    { id: 'taste_test', label: 'Taste Test' },
  ];

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-dark-surface border-l border-dark-border shadow-2xl z-50 flex flex-col">
      <div className="p-5 border-b border-dark-border bg-dark-surface/95 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-gray-100">{agent.display_name || 'Agent'}</h2>
            {agentData && (
              <div className="text-xs text-gray-400 mt-1">{agentData.archetype_display}</div>
            )}
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
        {activeTab === 'profile' && agentData && (
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-gray-400 mb-2">Archetype</h3>
              <div className="bg-dark-hover rounded p-2 text-sm">
                {agentData.archetype_display}
              </div>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-400 mb-2">Demographics</h3>
              <div className="bg-dark-hover rounded p-2 text-sm space-y-1">
                <div>Age: {agentData.age_bucket}</div>
                <div>Gender: {agentData.gender}</div>
                <div>Region: {agentData.region}</div>
                <div>Income: {agentData.income}</div>
              </div>
            </div>
            {agentData.taste_profile_json && agentData.taste_profile_json.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-400 mb-2">Taste Profile</h3>
                <div className="flex flex-wrap gap-2">
                  {agentData.taste_profile_json.map((tag, idx) => (
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
            {agentData.biography && (
              <div>
                <h3 className="text-sm font-semibold text-gray-400 mb-2">Biography</h3>
                <p className="text-sm text-gray-300">{agentData.biography}</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'chat' && (
          <ChatPanel agent={agent} filters={filters} />
        )}

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

