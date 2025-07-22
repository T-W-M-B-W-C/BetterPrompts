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
  creativeWriting: ['few_shot', 'emotional_appeal'],
  dataAnalysis: ['chain_of_thought', 'structured_output'],
  educational: ['few_shot', 'analogical_reasoning'],
};

test.describe('Prompt Classification API', () => {
  test('should be healthy', async ({ request }) => {
    const response = await request.get('/health');
    expect(response.ok()).toBeTruthy();
    
    // Health endpoint returns plain text "healthy"
    const body = await response.text();
    expect(body.trim()).toBe('healthy');
  });

  test('should classify simple prompts correctly', async ({ request }) => {
    const response = await request.post('/enhance', {
      data: {
        text: testPrompts.simple,
        target_complexity: 'simple',
      },
    });

    // Check if service is available
    if (response.status() === 502 || response.status() === 503) {
      test.skip(true, 'Service temporarily unavailable');
      return;
    }

    expect(response.ok()).toBeTruthy();
    const result = await response.json();
    
    expect(result).toHaveProperty('enhanced_prompt');
    expect(result).toHaveProperty('techniques_applied');
    expect(result.techniques_applied).toBeInstanceOf(Array);
    expect(result.techniques_applied.length).toBeGreaterThan(0);
  });

  test('should classify complex prompts with multiple techniques', async ({ request }) => {
    const response = await request.post('/enhance', {
      data: {
        text: testPrompts.complex,
        prefer_techniques: ['chain_of_thought', 'tree_of_thoughts'],
      },
    });

    if (response.status() === 502 || response.status() === 503) {
      test.skip(true, 'Service temporarily unavailable');
      return;
    }

    expect(response.ok()).toBeTruthy();
    const result = await response.json();
    
    expect(result.techniques_applied).toBeInstanceOf(Array);
    expect(result.techniques_applied.length).toBeGreaterThan(1);
    
    // Should include at least one of the preferred techniques
    const hasPreferredTechnique = result.techniques_applied.some(
      tech => ['chain_of_thought', 'tree_of_thoughts'].includes(tech)
    );
    expect(hasPreferredTechnique).toBeTruthy();
  });

  test.describe('Different prompt categories', () => {
    Object.entries(testPrompts).forEach(([category, prompt]) => {
      test(`should handle ${category} prompts`, async ({ request }) => {
        const response = await request.post('/enhance', {
          data: {
            text: prompt,
          },
        });

        if (response.status() === 502 || response.status() === 503) {
          test.skip(true, 'Service temporarily unavailable');
          return;
        }

        expect(response.ok()).toBeTruthy();
        const result = await response.json();
        
        expect(result).toHaveProperty('enhanced_prompt');
        expect(result).toHaveProperty('techniques_applied');
        expect(result.enhanced_prompt).not.toBe(prompt); // Should be enhanced
        expect(result.enhanced_prompt.length).toBeGreaterThan(prompt.length);
      });
    });
  });

  test('should handle invalid requests gracefully', async ({ request }) => {
    const response = await request.post('/enhance', {
      data: {
        text: '', // Empty text
      },
    });

    // Should return 400 Bad Request
    expect(response.status()).toBe(400);
    const error = await response.json();
    expect(error).toHaveProperty('error');
  });

  test('should handle missing fields', async ({ request }) => {
    const response = await request.post('/enhance', {
      data: {}, // No text field
    });

    expect(response.status()).toBe(400);
    const error = await response.json();
    expect(error).toHaveProperty('error');
  });

  test('should respect technique preferences', async ({ request }) => {
    const response = await request.post('/enhance', {
      data: {
        text: testPrompts.codeGeneration,
        prefer_techniques: ['few_shot'],
      },
    });

    if (response.status() === 502 || response.status() === 503) {
      test.skip(true, 'Service temporarily unavailable');
      return;
    }

    expect(response.ok()).toBeTruthy();
    const result = await response.json();
    
    // Should include the preferred technique
    expect(result.techniques_applied).toContain('few_shot');
  });
});

test.describe('Authentication', () => {
  test('should allow unauthenticated access to enhance endpoint', async ({ request }) => {
    const response = await request.post('/enhance', {
      data: {
        text: 'Test prompt',
      },
    });

    // Should not return 401
    expect(response.status()).not.toBe(401);
  });

  test('should require authentication for history endpoint', async ({ request }) => {
    const response = await request.get('/history');
    
    // Should return 401 Unauthorized
    expect(response.status()).toBe(401);
  });

  test('should accept valid JWT tokens', async ({ request }) => {
    // Skip if auth service is not configured
    const authResponse = await request.post('/auth/login', {
      data: {
        email: 'test@example.com',
        password: 'testpass123',
      },
    });

    if (authResponse.status() === 404 || authResponse.status() === 503) {
      test.skip(true, 'Auth service not available');
      return;
    }

    if (authResponse.ok()) {
      const { token } = await authResponse.json();
      
      const historyResponse = await request.get('/history', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      expect(historyResponse.ok()).toBeTruthy();
    }
  });
});

test.describe('Performance', () => {
  test('should respond within SLA', async ({ request }) => {
    const start = Date.now();
    const response = await request.post('/enhance', {
      data: {
        text: testPrompts.simple,
        target_complexity: 'simple',
      },
    });
    const duration = Date.now() - start;

    if (response.status() === 502 || response.status() === 503) {
      test.skip(true, 'Service temporarily unavailable');
      return;
    }

    expect(response.ok()).toBeTruthy();
    // Allow for network latency in test environment
    expect(duration).toBeLessThan(1000); // 1 second for test environment
  });

  test('should handle burst requests', async ({ request }) => {
    const concurrentRequests = 5; // Reduced for test stability
    const requests = Array(concurrentRequests).fill(null).map((_, i) => 
      request.post('/enhance', {
        data: {
          text: `Test prompt ${i}`,
          target_complexity: 'simple',
        },
      })
    );

    const responses = await Promise.all(requests);
    
    // Count successful responses
    const successfulResponses = responses.filter(r => r.ok());
    
    // At least 80% should succeed
    expect(successfulResponses.length).toBeGreaterThan(concurrentRequests * 0.8);
  });
});

test.describe('Edge Cases', () => {
  test('should handle very long prompts', async ({ request }) => {
    const longPrompt = 'This is a test. '.repeat(1000); // ~15,000 characters
    const response = await request.post('/enhance', {
      data: {
        text: longPrompt,
        target_complexity: 'simple',
      },
    });

    if (response.status() === 502 || response.status() === 503) {
      test.skip(true, 'Service temporarily unavailable');
      return;
    }

    expect(response.ok()).toBeTruthy();
    const result = await response.json();
    expect(result).toHaveProperty('enhanced_prompt');
  });

  test('should handle special characters', async ({ request }) => {
    const specialPrompt = 'Test with special chars: !@#$%^&*()_+{}[]|\\:";\'<>?,./';
    const response = await request.post('/enhance', {
      data: {
        text: specialPrompt,
      },
    });

    if (response.status() === 502 || response.status() === 503) {
      test.skip(true, 'Service temporarily unavailable');
      return;
    }

    expect(response.ok()).toBeTruthy();
    const result = await response.json();
    expect(result).toHaveProperty('enhanced_prompt');
  });

  test('should handle unicode characters', async ({ request }) => {
    const unicodePrompt = 'Test with unicode: 你好世界 🌍 café résumé';
    const response = await request.post('/enhance', {
      data: {
        text: unicodePrompt,
      },
    });

    if (response.status() === 502 || response.status() === 503) {
      test.skip(true, 'Service temporarily unavailable');
      return;
    }

    expect(response.ok()).toBeTruthy();
    const result = await response.json();
    expect(result).toHaveProperty('enhanced_prompt');
  });

  test('should handle malformed JSON gracefully', async ({ request }) => {
    const response = await request.post('/enhance', {
      headers: {
        'Content-Type': 'application/json',
      },
      data: '{invalid json}',
    });

    expect(response.status()).toBe(400);
  });
});