import { useState, useEffect } from 'react';

function ChatPanel({ agent, filters }) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);

  // Debug: Log agent prop
  useEffect(() => {
    console.log('ChatPanel agent prop:', agent);
    console.log('ChatPanel agent.id:', agent?.id);
  }, [agent]);
  
  // Reset messages when agent changes
  useEffect(() => {
    setMessages([]);
  }, [agent?.id]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || loading) return;
    
    // Check if agent and agent.id exist
    if (!agent) {
      setMessages([...messages, { 
        role: 'assistant', 
        content: 'Error: Agent information is missing. Please select an agent first.' 
      }]);
      return;
    }
    
    const agentId = agent.id || agent.uuid || agent.agent_id;
    if (!agentId) {
      console.error('Agent object:', agent);
      setMessages([...messages, { 
        role: 'assistant', 
        content: `Error: Agent ID not found. Agent object: ${JSON.stringify(agent)}` 
      }]);
      return;
    }

    const userMessage = { role: 'user', content: inputMessage };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInputMessage('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agent_id: agentId,
          messages: newMessages,
          mode: 'gpt', // Always use GPT
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }

      const data = await response.json();
      
      if (!data.response) {
        console.error('No response in data:', data);
        throw new Error('No response received from server');
      }
      
      setMessages([...newMessages, { role: 'assistant', content: data.response }]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = error.message || 'Sorry, I encountered an error. Please check the console for details.';
      setMessages([...newMessages, { role: 'assistant', content: `Error: ${errorMessage}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto space-y-4 mb-4 min-h-[400px]">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 text-sm py-8">
            <div className="text-gray-400 mb-2">Start a conversation with</div>
            <div className="font-semibold text-gray-200">{agent?.display_name || 'this agent'}</div>
            <div className="text-xs text-gray-600 mt-2">
              Ask about their preferences, habits, or opinions on fast-food choices
            </div>
          </div>
        )}
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-lg px-4 py-2.5 text-sm ${
                msg.role === 'user'
                  ? 'bg-accent-primary text-white shadow-lg shadow-accent-primary/30'
                  : 'bg-dark-hover text-gray-200 border border-dark-border'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-dark-hover border border-dark-border rounded-lg px-4 py-2.5 text-sm text-gray-400">
              <div className="flex space-x-1">
                <span className="animate-bounce">.</span>
                <span className="animate-bounce" style={{ animationDelay: '0.1s' }}>.</span>
                <span className="animate-bounce" style={{ animationDelay: '0.2s' }}>.</span>
              </div>
            </div>
          </div>
        )}
      </div>
      <form onSubmit={handleSend} className="flex gap-2 pt-4 border-t border-dark-border">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Type a message..."
          className="flex-1 bg-dark-hover border border-dark-border rounded-lg px-4 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-accent-primary"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !inputMessage.trim()}
          className="bg-accent-primary text-white rounded-lg px-4 py-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-accent-secondary transition-colors"
        >
          Send
        </button>
      </form>
    </div>
  );
}

export default ChatPanel;

