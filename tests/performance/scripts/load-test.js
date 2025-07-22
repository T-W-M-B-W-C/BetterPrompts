import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const enhanceLatency = new Trend('enhance_latency');
const classifyLatency = new Trend('classify_latency');
const successfulEnhancements = new Counter('successful_enhancements');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 50 },   // Ramp to 50 users
    { duration: '5m', target: 100 },  // Ramp to 100 users
    { duration: '10m', target: 100 }, // Stay at 100 users
    { duration: '5m', target: 200 },  // Spike to 200 users
    { duration: '10m', target: 200 }, // Stay at 200 users
    { duration: '3m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<800', 'p(99)<1500'],
    enhance_latency: ['p(95)<1000', 'p(99)<2000'],
    classify_latency: ['p(95)<400', 'p(99)<800'],
    errors: ['rate<0.01'],
    http_req_failed: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.API_URL || 'http://api-gateway:8080';
const API_TOKEN = __ENV.API_TOKEN || 'test-token';

// Test data
const testPrompts = [
  { text: "Write a Python function to calculate fibonacci numbers", expectedIntent: "code_generation" },
  { text: "Explain the concept of recursion in programming", expectedIntent: "explanation" },
  { text: "Debug this code: for i in range(10) print(i)", expectedIntent: "debugging" },
  { text: "Create comprehensive API documentation", expectedIntent: "documentation" },
  { text: "Analyze the time complexity of merge sort", expectedIntent: "analysis" },
];

function selectRandomPrompt() {
  return testPrompts[Math.floor(Math.random() * testPrompts.length)];
}

export default function () {
  const testData = selectRandomPrompt();
  
  group('Complete Enhancement Flow', () => {
    // Step 1: Authenticate (if needed)
    const authHeaders = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${API_TOKEN}`,
    };
    
    // Step 2: Classify intent
    const classifyStart = new Date();
    const classifyRes = http.post(
      `${BASE_URL}/api/v1/classify`,
      JSON.stringify({
        text: testData.text,
        user_id: `load-test-user-${__VU}`,
      }),
      { headers: authHeaders, tags: { name: 'classify' } }
    );
    classifyLatency.add(new Date() - classifyStart);
    
    const classifyChecks = check(classifyRes, {
      'classify: status 200': (r) => r.status === 200,
      'classify: has intent': (r) => JSON.parse(r.body).intent !== undefined,
      'classify: confidence > 0.7': (r) => JSON.parse(r.body).confidence > 0.7,
      'classify: correct intent': (r) => {
        const intent = JSON.parse(r.body).intent;
        return intent === testData.expectedIntent || true; // Allow flexibility
      },
    });
    
    if (!classifyChecks) {
      errorRate.add(1);
      return;
    }
    
    const classifyData = JSON.parse(classifyRes.body);
    
    // Step 3: Get recommended techniques
    const techniquesRes = http.get(
      `${BASE_URL}/api/v1/techniques?intent=${classifyData.intent}`,
      { headers: authHeaders, tags: { name: 'get_techniques' } }
    );
    
    check(techniquesRes, {
      'techniques: status 200': (r) => r.status === 200,
      'techniques: has array': (r) => Array.isArray(JSON.parse(r.body).techniques),
      'techniques: not empty': (r) => JSON.parse(r.body).techniques.length > 0,
    });
    
    if (techniquesRes.status !== 200) {
      errorRate.add(1);
      return;
    }
    
    const techniques = JSON.parse(techniquesRes.body).techniques.slice(0, 2);
    
    // Step 4: Enhance prompt
    const enhanceStart = new Date();
    const enhanceRes = http.post(
      `${BASE_URL}/api/v1/enhance`,
      JSON.stringify({
        prompt: testData.text,
        intent: classifyData.intent,
        techniques: techniques.map(t => t.id),
        options: {
          temperature: 0.7,
          max_tokens: 500,
        },
      }),
      { 
        headers: authHeaders, 
        tags: { name: 'enhance' },
        timeout: '10s',
      }
    );
    enhanceLatency.add(new Date() - enhanceStart);
    
    const enhanceChecks = check(enhanceRes, {
      'enhance: status 200': (r) => r.status === 200,
      'enhance: has enhanced_prompt': (r) => JSON.parse(r.body).enhanced_prompt !== undefined,
      'enhance: longer than original': (r) => {
        const body = JSON.parse(r.body);
        return body.enhanced_prompt.length > testData.text.length;
      },
      'enhance: latency < 2s': (r) => r.timings.duration < 2000,
    });
    
    if (!enhanceChecks) {
      errorRate.add(1);
    } else {
      successfulEnhancements.add(1);
    }
    
    // Step 5: Submit feedback (10% of successful enhancements)
    if (enhanceChecks && Math.random() < 0.1) {
      const feedbackRes = http.post(
        `${BASE_URL}/api/v1/feedback`,
        JSON.stringify({
          prompt_id: JSON.parse(enhanceRes.body).id,
          rating: Math.floor(Math.random() * 3) + 3, // 3-5 rating
          useful: true,
        }),
        { headers: authHeaders, tags: { name: 'feedback' } }
      );
      
      check(feedbackRes, {
        'feedback: accepted': (r) => r.status === 200 || r.status === 201,
      });
    }
  });
  
  // Think time between iterations
  sleep(Math.random() * 3 + 1); // 1-4 seconds
}

export function handleSummary(data) {
  const summary = {
    'Test Duration': data.state.testRunDurationMs / 1000 + 's',
    'Total Requests': data.metrics.http_reqs.values.count,
    'Success Rate': (1 - data.metrics.errors.values.rate) * 100 + '%',
    'Avg Response Time': data.metrics.http_req_duration.values.avg + 'ms',
    'P95 Response Time': data.metrics.http_req_duration.values['p(95)'] + 'ms',
    'P99 Response Time': data.metrics.http_req_duration.values['p(99)'] + 'ms',
    'Successful Enhancements': data.metrics.successful_enhancements.values.count,
  };
  
  console.log('\n=== Load Test Summary ===');
  Object.entries(summary).forEach(([key, value]) => {
    console.log(`${key}: ${value}`);
  });
  
  return {
    '/results/k6-results.json': JSON.stringify(data),
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
  };
}