import { useState } from 'react';

function ChatPanel({ agent, filters }) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || loading) return;

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
          agent_id: agent.id,
          messages: newMessages,
          mode: filters.use_gpt ? 'gpt' : 'mock',
        }),
      });

      const data = await response.json();
      setMessages([...newMessages, { role: 'assistant', content: data.response }]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages([...newMessages, { role: 'assistant', content: 'Sorry, I encountered an error.' }]);
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
            <div className="font-semibold text-gray-200">{agent.display_name || 'this agent'}</div>
            <div className="text-xs text-gray-500 mt-4">
              {filters.use_gpt ? 'GPT mode enabled' : 'Mock mode - responses are deterministic'}
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

