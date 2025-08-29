import { test, expect } from '@playwright/test';

// Test data for different prompt types
const testPrompts = {
  simple: 'Write a summary of this article',
  complex: 'Create a comprehensive business plan for a sustainable tech startup focusing on renewable energy solutions, including market analysis, financial projections, and go-to-market strategy',
  codeGeneration: 'Write a Python function to implement binary search',
  creativeWriting: 'Write a short story about a time traveler',
  dataAnalysis: 'Analyze sales trends and provide insights on seasonal patterns',
  educational: 'Explain quantum computing to a 10-year-old',
};

// Expected techniques for each prompt type
const expectedTechniques = {
  simple: ['zero_shot'],
  complex: ['chain_of_thought', 'tree_of_thoughts'],
  codeGeneration: ['few_shot', 'chain_of_thought'],
  creativeWriting: ['zero_shot', 'creative_prompting'],
  dataAnalysis: ['chain_of_thought', 'data_analysis'],
  educational: ['few_shot', 'educational_prompting'],
};

test.describe('Prompt Classification API', () => {
  test('should be healthy', async ({ request }) => {
    const response = await request.get('/health');
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body).toHaveProperty('status', 'healthy');
  });

  test('should classify simple prompts correctly', async ({ request }) => {
    const response = await request.post('/enhance', {
      data: {
        input: testPrompts.simple,
        options: {
          auto_apply: false,
        },
      },
    });

    expect(response.ok()).toBeTruthy();
    const result = await response.json();
    
    expect(result).toHaveProperty('intent');
    expect(result.intent).toHaveProperty('category');
    expect(result.intent).toHaveProperty('complexity');
    expect(result.intent.complexity).toBeLessThan(0.5);
    expect(result).toHaveProperty('techniques');
    expect(result.techniques).toContain('zero_shot');
  });

  test('should classify complex prompts with multiple techniques', async ({ request }) => {
    const response = await request.post('/enhance', {
      data: {
        input: testPrompts.complex,
        options: {
          auto_apply: false,
        },
      },
    });

    expect(response.ok()).toBeTruthy();
    const result = await response.json();
    
    expect(result.intent.complexity).toBeGreaterThan(0.7);
    expect(result.techniques).toEqual(expect.arrayContaining(['chain_of_thought', 'tree_of_thoughts']));
    expect(result.techniques.length).toBeGreaterThan(1);
  });

  test.describe('Different prompt categories', () => {
    Object.entries(testPrompts).forEach(([category, prompt]) => {
      test(`should handle ${category} prompts`, async ({ request }) => {
        const response = await request.post('/enhance', {
          data: {
            input: prompt,
            options: {
              auto_apply: false,
            },
          },
        });

        expect(response.ok()).toBeTruthy();
        const result = await response.json();
        
        expect(result).toHaveProperty('intent');
        expect(result).toHaveProperty('techniques');
        expect(result).toHaveProperty('enhanced_prompt');
        
        // Verify at least one expected technique is suggested
        const suggestedTechniques = result.techniques;
        const expectedForCategory = expectedTechniques[category];
        const hasExpectedTechnique = expectedForCategory.some(tech => 
          suggestedTechniques.includes(tech)
        );
        expect(hasExpectedTechnique).toBeTruthy();
      });
    });
  });

  test('should apply techniques when requested', async ({ request }) => {
    const response = await request.post('/enhance', {
      data: {
        input: testPrompts.codeGeneration,
        options: {
          auto_apply: true,
        },
      },
    });

    expect(response.ok()).toBeTruthy();
    const result = await response.json();
    
    expect(result).toHaveProperty('enhanced_prompt');
    expect(result.enhanced_prompt).not.toBe(testPrompts.codeGeneration);
    expect(result.enhanced_prompt.length).toBeGreaterThan(testPrompts.codeGeneration.length);
    
    // Should contain technique markers
    expect(result.enhanced_prompt).toMatch(/step|example|approach/i);
  });

  test('should handle invalid requests gracefully', async ({ request }) => {
    const response = await request.post('/enhance', {
      data: {
        input: '',
      },
    });

    expect(response.status()).toBe(400);
    const error = await response.json();
    expect(error).toHaveProperty('error');
    expect(error.error).toContain('Input cannot be empty');
  });

  test('should respect rate limiting', async ({ request }) => {
    const requests = Array(100).fill(null).map(() => 
      request.post('/enhance', {
        data: {
          input: 'Test prompt',
          options: { auto_apply: false },
        },
      })
    );

    const responses = await Promise.all(requests);
    const rateLimited = responses.some(r => r.status() === 429);
    expect(rateLimited).toBeTruthy();
  });

  test('should track effectiveness when feedback provided', async ({ request }) => {
    // First, enhance a prompt
    const enhanceResponse = await request.post('/enhance', {
      data: {
        input: testPrompts.dataAnalysis,
        options: { auto_apply: true },
      },
    });

    const { request_id } = await enhanceResponse.json();

    // Then provide feedback
    const feedbackResponse = await request.post('/feedback', {
      data: {
        request_id,
        effectiveness: 0.9,
        user_rating: 5,
      },
    });

    expect(feedbackResponse.ok()).toBeTruthy();
    const feedbackResult = await feedbackResponse.json();
    expect(feedbackResult).toHaveProperty('status', 'recorded');
  });
});

test.describe('Authentication', () => {
  test('should require authentication for user-specific endpoints', async ({ request }) => {
    const response = await request.get('/user/preferences');
    expect(response.status()).toBe(401);
  });

  test('should accept valid JWT tokens', async ({ request }) => {
    // First, get a token
    const authResponse = await request.post('/auth/login', {
      data: {
        username: 'testuser',
        password: 'testpass',
      },
    });

    if (authResponse.ok()) {
      const { token } = await authResponse.json();
      
      const preferencesResponse = await request.get('/user/preferences', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      expect(preferencesResponse.ok()).toBeTruthy();
    }
  });
});

test.describe('Performance', () => {
  test('should respond within SLA', async ({ request }) => {
    const start = Date.now();
    const response = await request.post('/enhance', {
      data: {
        input: testPrompts.simple,
        options: { auto_apply: false },
      },
    });
    const duration = Date.now() - start;

    expect(response.ok()).toBeTruthy();
    expect(duration).toBeLessThan(200); // p95 < 200ms SLA
  });

  test('should handle concurrent requests', async ({ request }) => {
    const concurrentRequests = 10;
    const requests = Array(concurrentRequests).fill(null).map((_, i) => 
      request.post('/enhance', {
        data: {
          input: `Test prompt ${i}`,
          options: { auto_apply: false },
        },
      })
    );

    const start = Date.now();
    const responses = await Promise.all(requests);
    const duration = Date.now() - start;

    const successfulResponses = responses.filter(r => r.ok());
    expect(successfulResponses.length).toBe(concurrentRequests);
    
    // Average response time should still be reasonable
    const avgResponseTime = duration / concurrentRequests;
    expect(avgResponseTime).toBeLessThan(500);
  });
});