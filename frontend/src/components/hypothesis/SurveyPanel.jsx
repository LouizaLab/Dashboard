import { useState, useEffect } from 'react';

function SurveyPanel({ agent, filters }) {
  const [questions, setQuestions] = useState([]);
  const [selectedQuestions, setSelectedQuestions] = useState([]);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadQuestions();
  }, []);

  const loadQuestions = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/survey/questions/');
      const data = await response.json();
      // Handle paginated or non-paginated response
      if (Array.isArray(data)) {
        setQuestions(data);
      } else if (data.results) {
        setQuestions(data.results);
      } else {
        setQuestions([]);
      }
    } catch (error) {
      console.error('Failed to load questions:', error);
    }
  };

  const handleRunSurvey = async () => {
    if (selectedQuestions.length === 0) return;

    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/survey/run/', {
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
          questions: selectedQuestions,
          mode: 'gpt', // Always use GPT
        }),
      });

      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Survey error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-gray-400 mb-2">Select Questions</h3>
        <div className="space-y-2 max-h-60 overflow-y-auto">
          {questions.map((q) => (
            <label
              key={q.id}
              className="flex items-start space-x-2 bg-dark-hover rounded p-2 cursor-pointer hover:bg-dark-border transition-colors"
            >
              <input
                type="checkbox"
                checked={selectedQuestions.includes(q.id)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedQuestions([...selectedQuestions, q.id]);
                  } else {
                    setSelectedQuestions(selectedQuestions.filter((id) => id !== q.id));
                  }
                }}
                className="mt-1"
              />
              <span className="text-sm text-gray-300 flex-1">{q.question_text}</span>
            </label>
          ))}
        </div>
      </div>

      <button
        onClick={handleRunSurvey}
        disabled={selectedQuestions.length === 0 || loading}
        className="w-full bg-accent-primary text-white rounded px-4 py-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? 'Running Survey...' : `Run Survey (${selectedQuestions.length} questions)`}
      </button>

      {results && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-gray-400">Results</h3>
          {Object.entries(results.aggregated_results || {}).map(([qId, result]) => (
            <div key={qId} className="bg-dark-hover rounded p-3">
              <div className="text-sm font-medium text-gray-200 mb-2">{result.question_text}</div>
              {result.average_score && (
                <div className="text-xs text-gray-400">
                  Average Score: {result.average_score.toFixed(2)}/5
                </div>
              )}
              {result.distribution && Object.keys(result.distribution).length > 0 && (
                <div className="mt-2 text-xs text-gray-400">
                  {Object.entries(result.distribution).map(([key, val]) => (
                    <div key={key}>
                      {key}: {val}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default SurveyPanel;

