import { Page } from '@playwright/test';

/**
 * Search Test Utilities
 * Helpers for testing search and filter functionality
 */
export class SearchTestUtils {
  /**
   * Wait for search debounce
   * The frontend has a 500ms debounce on search input
   */
  static async waitForSearchDebounce(page: Page): Promise<void> {
    await page.waitForTimeout(600);
  }

  /**
   * Generate search queries for edge cases
   */
  static getEdgeCaseQueries(): string[] {
    return [
      '', // Empty search
      ' ', // Single space
      '   ', // Multiple spaces
      'a', // Single character
      'ab', // Two characters
      'SELECT * FROM users WHERE 1=1', // SQL injection attempt
      '<script>alert("xss")</script>', // XSS attempt
      '../../etc/passwd', // Path traversal attempt
      'prompt'.repeat(100), // Very long query
      '特殊字符测试', // Unicode characters
      '🚀🎉😊', // Emojis
      'prompt\nwith\nnewlines', // Newlines
      'prompt\twith\ttabs', // Tabs
      'PROMPT', // All caps
      'PrOmPt', // Mixed case
      '"exact match"', // Quoted search
      'prompt*', // Wildcard
      'prompt?', // Question mark
      'prompt!', // Exclamation
      'prompt@example', // Email-like
      '#hashtag', // Hashtag
      'prompt AND enhance', // Boolean operators
      'prompt OR enhance',
      'NOT prompt',
      '(prompt)', // Parentheses
      '[prompt]', // Brackets
      '{prompt}', // Braces
      'prompt+enhance', // Plus sign
      'prompt-enhance', // Hyphen
      'prompt_enhance', // Underscore
      'prompt.enhance', // Dot
      'prompt,enhance', // Comma
      'prompt;enhance', // Semicolon
      'prompt:enhance', // Colon
      'prompt/enhance', // Slash
      'prompt\\enhance', // Backslash
      'prompt|enhance', // Pipe
      'prompt~enhance', // Tilde
      'prompt`enhance', // Backtick
      'prompt$enhance', // Dollar sign
      'prompt%enhance', // Percent
      'prompt^enhance', // Caret
      'prompt&enhance', // Ampersand
      'prompt=enhance', // Equals
    ];
  }

  /**
   * Generate filter combinations for testing
   */
  static getFilterCombinations(): Array<{
    intent?: string;
    technique?: string;
    search?: string;
    description: string;
  }> {
    return [
      {
        description: 'No filters (show all)'
      },
      {
        intent: 'code_generation',
        description: 'Single intent filter'
      },
      {
        technique: 'chain_of_thought',
        description: 'Single technique filter'
      },
      {
        search: 'function',
        description: 'Search only'
      },
      {
        intent: 'code_generation',
        technique: 'chain_of_thought',
        description: 'Intent and technique filters'
      },
      {
        intent: 'code_generation',
        search: 'function',
        description: 'Intent filter with search'
      },
      {
        technique: 'chain_of_thought',
        search: 'analyze',
        description: 'Technique filter with search'
      },
      {
        intent: 'analysis',
        technique: 'structured_output',
        search: 'market',
        description: 'All filters combined'
      }
    ];
  }

  /**
   * Verify search results match query
   */
  static async verifySearchResults(
    page: Page,
    query: string,
    resultSelector: string
  ): Promise<{
    matches: boolean;
    totalResults: number;
    matchingResults: number;
  }> {
    // Get all result elements
    const results = await page.locator(resultSelector).all();
    const totalResults = results.length;
    let matchingResults = 0;

    // Check each result for the query
    const queryLower = query.toLowerCase();
    for (const result of results) {
      const text = (await result.textContent() || '').toLowerCase();
      if (text.includes(queryLower)) {
        matchingResults++;
      }
    }

    return {
      matches: matchingResults === totalResults && totalResults > 0,
      totalResults,
      matchingResults
    };
  }

  /**
   * Test search performance
   */
  static async measureSearchPerformance(
    page: Page,
    searchAction: () => Promise<void>
  ): Promise<{
    duration: number;
    withinSLA: boolean;
    SLA: number;
  }> {
    const SLA = 500; // 500ms SLA for search
    const startTime = Date.now();
    
    await searchAction();
    
    const duration = Date.now() - startTime;
    
    return {
      duration,
      withinSLA: duration <= SLA,
      SLA
    };
  }

  /**
   * Generate test data with specific searchable content
   */
  static generateSearchableData(): Array<{
    prompt: string;
    searchTerms: string[];
    intent: string;
    techniques: string[];
  }> {
    return [
      {
        prompt: 'Write a Python function to calculate the factorial of a number',
        searchTerms: ['python', 'function', 'factorial', 'calculate'],
        intent: 'code_generation',
        techniques: ['chain_of_thought', 'structured_output']
      },
      {
        prompt: 'Analyze the market trends for renewable energy in 2024',
        searchTerms: ['analyze', 'market', 'trends', 'renewable', 'energy', '2024'],
        intent: 'analysis',
        techniques: ['step_by_step', 'perspective_taking']
      },
      {
        prompt: 'Create a comprehensive business plan for a SaaS startup',
        searchTerms: ['create', 'business', 'plan', 'saas', 'startup', 'comprehensive'],
        intent: 'creative_writing',
        techniques: ['structured_output', 'few_shot']
      },
      {
        prompt: 'Debug this JavaScript code that causes memory leaks',
        searchTerms: ['debug', 'javascript', 'code', 'memory', 'leaks'],
        intent: 'problem_solving',
        techniques: ['chain_of_thought', 'socratic_questioning']
      },
      {
        prompt: 'Explain quantum computing to a 10-year-old child',
        searchTerms: ['explain', 'quantum', 'computing', 'child', '10-year-old'],
        intent: 'explanation',
        techniques: ['analogical_reasoning', 'simplification']
      }
    ];
  }

  /**
   * Verify filter options are populated correctly
   */
  static async verifyFilterOptions(
    page: Page,
    filterSelector: string,
    expectedOptions: string[]
  ): Promise<boolean> {
    const options = await page.locator(`${filterSelector} option`).all();
    const actualOptions: string[] = [];
    
    for (const option of options) {
      const value = await option.getAttribute('value');
      const text = await option.textContent();
      if (value && value !== 'all' && text) {
        actualOptions.push(text.trim());
      }
    }
    
    // Check if all expected options are present
    const allPresent = expectedOptions.every(expected => 
      actualOptions.includes(expected)
    );
    
    return allPresent;
  }

  /**
   * Test search highlighting (if implemented)
   */
  static async verifySearchHighlighting(
    page: Page,
    query: string,
    highlightSelector: string = 'mark, .highlight'
  ): Promise<boolean> {
    const highlights = await page.locator(highlightSelector).all();
    
    if (highlights.length === 0) {
      // Highlighting might not be implemented
      return true;
    }
    
    // Check if highlighted text matches query
    for (const highlight of highlights) {
      const text = (await highlight.textContent() || '').toLowerCase();
      if (!text.includes(query.toLowerCase())) {
        return false;
      }
    }
    
    return true;
  }
}