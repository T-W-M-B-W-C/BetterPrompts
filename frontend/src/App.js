import React, { useState } from 'react';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const techniqueDescriptions = {
  'chain_of_thought': '🔗 Breaking down reasoning into logical steps',
  'few_shot': '📚 Learning from examples',
  'tree_of_thoughts': '🌳 Exploring multiple reasoning paths',
  'step_by_step': '📝 Sequential instruction breakdown',
  'zero_shot': '🎯 Direct task understanding',
  'role_play': '🎭 Adopting specific perspectives',
  'constraints': '⚡ Working within defined boundaries',
  'self_consistency': '🔄 Multiple reasoning validation',
  'analogical': '🔀 Drawing parallels and comparisons',
  'structured_output': '📊 Organized response formatting'
};

function App() {
  const [prompt, setPrompt] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showThinking, setShowThinking] = useState(true);

  const enhance = async () => {
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch(`${API_URL}/api/v1/enhance`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: prompt, user_id: 'demo' })
      });
      setResult(await res.json());
    } catch (err) {
      setResult({ error: err.message });
    }
    setLoading(false);
  };

  return (
    <div style={{ maxWidth: '900px', margin: '40px auto', padding: '20px', fontFamily: 'system-ui' }}>
      <h1 style={{ borderBottom: '2px solid #333', paddingBottom: '10px' }}>BetterPrompts</h1>
      <p style={{ color: '#666', marginBottom: '20px' }}>
        Transform your prompts using advanced techniques automatically
      </p>
      
      <textarea
        value={prompt}
        onChange={e => setPrompt(e.target.value)}
        placeholder="Enter your prompt... e.g., 'Write a story about a robot' or 'Explain quantum computing'"
        style={{ 
          width: '100%', 
          height: '120px', 
          marginBottom: '10px', 
          padding: '12px',
          fontSize: '14px',
          border: '1px solid #ddd',
          borderRadius: '4px',
          resize: 'vertical'
        }}
      />
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
        <button 
          onClick={enhance} 
          disabled={!prompt || loading}
          style={{ 
            padding: '10px 24px',
            background: loading ? '#999' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: !prompt || loading ? 'not-allowed' : 'pointer',
            fontSize: '16px'
          }}
        >
          {loading ? '🔄 Analyzing...' : '✨ Enhance Prompt'}
        </button>
        <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
          <input 
            type="checkbox" 
            checked={showThinking}
            onChange={e => setShowThinking(e.target.checked)}
            style={{ marginRight: '5px' }}
          />
          Show thinking process
        </label>
      </div>

      {loading && (
        <div style={{ 
          background: 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)',
          backgroundSize: '200% 100%',
          animation: 'loading 1.5s infinite',
          height: '100px',
          borderRadius: '4px',
          marginBottom: '20px'
        }}/>
      )}

      {result && !result.error && (
        <div>
          {showThinking && result.intent && (
            <div style={{ 
              background: '#f8f9fa', 
              padding: '15px', 
              borderRadius: '4px',
              marginBottom: '15px',
              borderLeft: '4px solid #28a745'
            }}>
              <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', color: '#28a745' }}>
                🧠 Analysis
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '14px' }}>
                <div>
                  <strong>Intent:</strong> {result.intent || 'Analyzing...'}
                </div>
                <div>
                  <strong>Complexity:</strong> {result.complexity || 'Determining...'}
                </div>
                <div>
                  <strong>Confidence:</strong> {result.confidence ? `${(result.confidence * 100).toFixed(0)}%` : 'Calculating...'}
                </div>
                <div>
                  <strong>Processing:</strong> {result.processing_time_ms ? `${result.processing_time_ms.toFixed(0)}ms` : 'N/A'}
                </div>
              </div>
            </div>
          )}

          {showThinking && result.techniques_used && result.techniques_used.length > 0 && (
            <div style={{ 
              background: '#fff3cd', 
              padding: '15px', 
              borderRadius: '4px',
              marginBottom: '15px',
              borderLeft: '4px solid #ffc107'
            }}>
              <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', color: '#856404' }}>
                🎯 Techniques Selected
              </h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {result.techniques_used.map(t => (
                  <div key={t} style={{
                    background: 'white',
                    padding: '6px 12px',
                    borderRadius: '20px',
                    fontSize: '13px',
                    border: '1px solid #ffc107'
                  }}>
                    {techniqueDescriptions[t] || `✓ ${t}`}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div style={{ 
            background: '#d4edda', 
            padding: '20px', 
            borderRadius: '4px',
            borderLeft: '4px solid #28a745'
          }}>
            <h3 style={{ margin: '0 0 15px 0', color: '#155724' }}>
              ✨ Enhanced Prompt
            </h3>
            <div style={{ 
              background: 'white', 
              padding: '15px',
              borderRadius: '4px',
              fontFamily: 'monospace',
              fontSize: '14px',
              lineHeight: '1.5',
              whiteSpace: 'pre-wrap'
            }}>
              {result.enhanced_text || result.enhanced_prompt}
            </div>
            <button
              onClick={() => navigator.clipboard.writeText(result.enhanced_text || result.enhanced_prompt)}
              style={{
                marginTop: '10px',
                padding: '6px 12px',
                background: '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '13px'
              }}
            >
              📋 Copy to Clipboard
            </button>
          </div>
        </div>
      )}

      {result && result.error && (
        <div style={{ 
          background: '#f8d7da', 
          padding: '15px', 
          borderRadius: '4px',
          borderLeft: '4px solid #dc3545',
          color: '#721c24'
        }}>
          <strong>Error:</strong> {result.error}
        </div>
      )}

      <style>{`
        @keyframes loading {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
      `}</style>
    </div>
  );
}

export default App;