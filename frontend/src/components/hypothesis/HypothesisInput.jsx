import { useState } from 'react';

function HypothesisInput({ onRun, loading }) {
  const [inputText, setInputText] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputText.trim()) {
      onRun(inputText);
      setInputText('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative">
      <input
        type="text"
        value={inputText}
        onChange={(e) => setInputText(e.target.value)}
        placeholder="type your question or hypothesis and test it on simulated users"
        className="w-full bg-dark-surface border border-dark-border rounded-xl px-5 py-4 pr-14 text-gray-100 placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500"
        disabled={loading}
      />
      <button
        type="submit"
        disabled={loading || !inputText.trim()}
        className="absolute right-3 top-1/2 -translate-y-1/2 p-2 text-gray-400 hover:text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
        </svg>
      </button>
      {loading && (
        <div className="absolute right-14 top-1/2 -translate-y-1/2">
          <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-400 border-t-transparent"></div>
        </div>
      )}
    </form>
  );
}

export default HypothesisInput;
