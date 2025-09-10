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
    <>
      <header style={{ background: '#ffffff', borderBottom: '1px solid #eeeeee' }}>
        <div style={{ maxWidth: '900px', margin: '0 auto', padding: '10px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 800, color: '#198754' }}>
            <img src="/favicon.ico" alt="BetterPrompts logo" style={{ width: '20px', height: '20px', borderRadius: '4px' }} />
            <span>BetterPrompts</span>
          </div>
          <nav style={{ display: 'flex', gap: '14px' }}>
            <a href="#" style={{ color: '#198754', textDecoration: 'none' }}>Docs</a>
            <a href="#" style={{ color: '#198754', textDecoration: 'none' }}>Pricing</a>
            <a href="#" style={{ color: '#198754', textDecoration: 'none' }}>Blog</a>
            <a href="#" style={{ color: '#198754', textDecoration: 'none' }}>Contact</a>
            <a href="#" style={{ color: '#198754', textDecoration: 'none' }}>GitHub</a>
          </nav>
        </div>
      </header>
      <div
        style={{
          position: 'relative',
          width: '100%',
          height: '260px',
          margin: 0,
          borderRadius: 0,
          overflow: 'hidden',
          backgroundImage: "url('/images/bamboo.jpg')",
          backgroundSize: 'cover',
          backgroundPosition: 'center'
        }}
        aria-label="Hero image"
        role="img"
      >
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: 'linear-gradient(180deg, rgba(0,0,0,0.35) 0%, rgba(0,0,0,0.45) 60%, rgba(0,0,0,0.55) 100%)'
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: 'column',
            padding: '0 24px',
            textAlign: 'center',
            textShadow: '0 3px 10px rgba(0,0,0,0.45)'
          }}
        >
          <div style={{ fontSize: '48px', fontWeight: 800, letterSpacing: '0.4px', lineHeight: 1.1, color: '#ffffff' }}>BetterPrompts</div>
          <div style={{ fontSize: '20px', opacity: 0.98, marginTop: '6px', color: '#ffffff' }}>Transform your prompts using advanced techniques automatically</div>
        </div>
      </div>
      <div style={{ maxWidth: '900px', margin: '8px auto 40px', padding: '10px 20px 20px 20px', fontFamily: 'system-ui' }}>
        <h2
          style={{
            borderBottom: '2px solid #333',
            color: '#198754',
            textAlign: 'center',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            height: '72px',
            margin: '0 0 16px 0'
          }}
        >
          Transform your prompts using advanced techniques automatically
        </h2>
        <div style={{ display: 'flex', justifyContent: 'space-evenly', gap: '16px', margin: '8px 0 16px 0' }}>
          <p style={{ color: '#000', lineHeight: 1.5, flex: 1 }}>
            BetterPrompts accelerates your workflow by turning vague ideas into clear, structured instructions. With intent-aware techniques and consistent formatting, you reduce revision cycles, improve clarity, and get high-quality results faster.
          </p>
          <p style={{ color: '#000', lineHeight: 1.5, flex: 1 }}>
            Thoughtful elaboration guides models to the target outcome—specifying goals, constraints, style, and structure. This focus not only improves response relevance and coherence, but also builds better prompting habits over time.
          </p>
        </div>
        <div style={{ width: '100%', background: '#f2f2f2', border: '1px solid #e5e5e5', borderRadius: '6px', padding: '28px 28px', margin: '24px 0 24px 0' }}>
          <h3 style={{ margin: '0 0 8px 0', color: '#198754', fontSize: '18px' }}>
            Why goals, constraints, style, and structure improve results
          </h3>
          <p style={{ color: '#000', margin: '12px 0 12px 0', lineHeight: 1.55 }}>
            When you define <strong>goals</strong>, the model understands the destination—what “good” looks like—so it can prioritize information and make sharper trade‑offs. Clear <strong>constraints</strong> (time, scope, sources, compliance) reduce ambiguity and prevent detours, which directly improves accuracy, safety, and consistency.
          </p>
          <p style={{ color: '#000', margin: 0, lineHeight: 1.55 }}>
            Choosing an appropriate <strong>style</strong> (tone, audience level, format) and imposing <strong>structure</strong> (sections, bullet points, JSON schema) creates a predictable shape for the output. This makes answers easier to evaluate, compare, and reuse—while guiding the model to produce focused, verifiable content that better serves your intent.
          </p>
        </div>
        <div style={{ width: '100%', background: '#f2f2f2', border: '1px solid #e5e5e5', borderRadius: '6px', padding: '28px 28px', margin: '24px 0 24px 0' }}>
          <h3 style={{ margin: '0 0 8px 0', color: '#198754', fontSize: '18px' }}>
            What to expect from BetterPrompts
          </h3>
          <p style={{ color: '#000', margin: '12px 0 0 0', lineHeight: 1.55 }}>
            BetterPrompts refines your input into clear, goal-driven instructions with explicit constraints and structure. Expect more relevant, verifiable outputs; fewer rewrites; and consistent formatting you can reuse across tasks and teams.
          </p>
        </div>
        <div
          style={{
            position: 'relative',
            left: '50%',
            right: '50%',
            marginLeft: '-50vw',
            marginRight: '-50vw',
            width: '100vw',
            height: '260px',
            marginTop: '56px',
            marginBottom: '24px',
            overflow: 'hidden',
            backgroundImage: "url('/images/bamboo2.jpg')",
            backgroundSize: 'cover',
            backgroundPosition: 'center'
          }}
          aria-label="Secondary hero image"
          role="img"
        >
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background: 'linear-gradient(180deg, rgba(0,0,0,0.35) 0%, rgba(0,0,0,0.45) 60%, rgba(0,0,0,0.55) 100%)'
            }}
          />
        </div>
      
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '80px 0' }}>
        <h2 style={{ textAlign: 'center', margin: '0 0 16px 0', color: '#198754' }}>
          Try BetterPrompts now
        </h2>
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
              background: loading ? '#999' : '#198754',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: !prompt || loading ? 'not-allowed' : 'pointer',
              fontSize: '16px'
            }}
          >
            {loading ? '🔄 Analyzing...' : '✨ Enhance Prompt'}
          </button>
          <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', color: '#198754' }}>
            <input 
              type="checkbox" 
              checked={showThinking}
              onChange={e => setShowThinking(e.target.checked)}
              style={{ marginRight: '5px', accentColor: '#198754' }}
            />
            Show thinking process
          </label>
        </div>
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
          body { margin: 0; }
          @keyframes loading {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
          }
        `}</style>
      </div>
      <div
        style={{
          position: 'relative',
          width: '100%',
          height: '260px',
          margin: 0,
          borderRadius: 0,
          overflow: 'hidden',
          backgroundImage: "url('/images/bamboo3.jpg')",
          backgroundSize: 'cover',
          backgroundPosition: 'center'
        }}
        aria-label="Bottom hero image"
        role="img"
      >
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: 'linear-gradient(180deg, rgba(0,0,0,0.35) 0%, rgba(0,0,0,0.45) 60%, rgba(0,0,0,0.55) 100%)'
          }}
        />
      </div>
      <footer style={{ background: '#ffffff', borderTop: '1px solid #eeeeee', padding: '16px 20px' }}>
        <div style={{ maxWidth: '900px', margin: '0 auto', display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '14px', fontSize: '14px' }}>
          <a href="#" style={{ color: '#198754', textDecoration: 'none' }}>Docs</a>
          <a href="#" style={{ color: '#198754', textDecoration: 'none' }}>Privacy</a>
          <a href="#" style={{ color: '#198754', textDecoration: 'none' }}>Terms</a>
          <a href="#" style={{ color: '#198754', textDecoration: 'none' }}>Contact</a>
          <a href="#" style={{ color: '#198754', textDecoration: 'none' }}>GitHub</a>
        </div>
      </footer>
    </>
  );
}

export default App;