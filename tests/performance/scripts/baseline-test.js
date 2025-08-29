import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const apiLatency = new Trend('api_latency');

// Test configuration
export const options = {
  stages: [
    { duration: '1m', target: 10 },  // Ramp up to 10 users
    { duration: '3m', target: 10 },  // Stay at 10 users
    { duration: '1m', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
    errors: ['rate<0.05'],           // Error rate under 5%
  },
};

const BASE_URL = __ENV.API_URL || 'http://api-gateway:8080';

// Test data
const prompts = [
  "Write a function to sort an array",
  "Explain how machine learning works",
  "Debug this code: print(x)",
  "Create a README for my project",
  "Analyze the performance of this algorithm"
];

export default function () {
  // Select random prompt
  const prompt = prompts[Math.floor(Math.random() * prompts.length)];
  
  // Test 1: Health check
  const healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    'health check status is 200': (r) => r.status === 200,
  });
  
  // Test 2: Classify intent
  const classifyPayload = JSON.stringify({
    text: prompt,
    user_id: `test-user-${__VU}`,
  });
  
  const classifyParams = {
    headers: {
      'Content-Type': 'application/json',
    },
  };
  
  const startTime = new Date();
  const classifyRes = http.post(
    `${BASE_URL}/api/v1/classify`,
    classifyPayload,
    classifyParams
  );
  const latency = new Date() - startTime;
  
  apiLatency.add(latency);
  
  const classifySuccess = check(classifyRes, {
    'classify status is 200': (r) => r.status === 200,
    'classify has intent': (r) => {
      const body = JSON.parse(r.body);
      return body.intent !== undefined;
    },
    'classify latency < 300ms': (r) => r.timings.duration < 300,
  });
  
  if (!classifySuccess) {
    errorRate.add(1);
  }
  
  // Test 3: Get techniques
  if (classifyRes.status === 200) {
    const intent = JSON.parse(classifyRes.body).intent;
    const techniquesRes = http.get(`${BASE_URL}/api/v1/techniques?intent=${intent}`);
    
    check(techniquesRes, {
      'techniques status is 200': (r) => r.status === 200,
      'has techniques array': (r) => {
        const body = JSON.parse(r.body);
        return Array.isArray(body.techniques);
      },
    });
  }
  
  // Think time
  sleep(Math.random() * 2 + 1); // 1-3 seconds
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    '/results/baseline.json': JSON.stringify(data),
  };
}