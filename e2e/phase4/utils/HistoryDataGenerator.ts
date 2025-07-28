/**
 * History Data Generator
 * Generates test data for enhancement history testing
 */
export class HistoryDataGenerator {
  // Sample prompts for different categories
  private static readonly PROMPT_TEMPLATES = {
    programming: [
      "Write a function to calculate fibonacci numbers",
      "Explain how to implement a binary search tree",
      "Create a REST API endpoint for user authentication",
      "Debug this JavaScript code that's throwing an error",
      "Optimize this SQL query for better performance"
    ],
    writing: [
      "Write an introduction for an article about climate change",
      "Create a compelling product description for a smartwatch",
      "Draft an email to request a meeting with a client",
      "Compose a social media post about our new product launch",
      "Write a conclusion for a research paper on AI ethics"
    ],
    analysis: [
      "Analyze the market trends for electric vehicles",
      "Compare the pros and cons of remote work",
      "Evaluate the effectiveness of this marketing campaign",
      "Review this business proposal and provide feedback",
      "Assess the risks of implementing this new system"
    ],
    creative: [
      "Generate ideas for a mobile app that helps people learn languages",
      "Create a storyline for a science fiction short story",
      "Design a logo concept for a sustainable fashion brand",
      "Brainstorm names for a new coffee shop",
      "Develop a concept for an educational board game"
    ]
  };

  // Techniques that might be applied
  private static readonly TECHNIQUES = [
    'chain_of_thought',
    'few_shot',
    'step_by_step',
    'structured_output',
    'role_playing',
    'socratic_questioning',
    'analogical_reasoning',
    'perspective_taking',
    'constraint_setting',
    'tree_of_thoughts'
  ];

  // Intents
  private static readonly INTENTS = [
    'code_generation',
    'explanation',
    'analysis',
    'creative_writing',
    'problem_solving',
    'data_analysis',
    'question_answering',
    'summarization',
    'translation',
    'ideation'
  ];

  // Complexity levels
  private static readonly COMPLEXITY_LEVELS = ['simple', 'moderate', 'complex'];

  /**
   * Generate a single test prompt
   */
  static generatePrompt(options?: {
    category?: keyof typeof HistoryDataGenerator.PROMPT_TEMPLATES;
    includeSpecialChars?: boolean;
    length?: 'short' | 'medium' | 'long';
  }): string {
    const category = options?.category || this.randomChoice(Object.keys(this.PROMPT_TEMPLATES) as any);
    const prompts = this.PROMPT_TEMPLATES[category];
    let prompt = this.randomChoice(prompts);

    // Add length variations
    if (options?.length === 'long') {
      prompt += ` Please provide a detailed explanation with examples and best practices. Include code samples where relevant and discuss potential edge cases.`;
    } else if (options?.length === 'short') {
      prompt = prompt.split(' ').slice(0, 5).join(' ');
    }

    // Add special characters if requested
    if (options?.includeSpecialChars) {
      const specialChars = ['!', '@', '#', '$', '%', '&', '*', '(', ')', '[', ']', '{', '}'];
      prompt += ` ${this.randomChoice(specialChars)} Special case test`;
    }

    return prompt;
  }

  /**
   * Generate enhanced version of a prompt
   */
  static generateEnhancedPrompt(originalPrompt: string, techniques: string[]): string {
    let enhanced = originalPrompt;

    // Apply technique-specific enhancements
    if (techniques.includes('chain_of_thought')) {
      enhanced = `Let's think about this step by step. ${enhanced} First, I'll identify the key components...`;
    }
    
    if (techniques.includes('structured_output')) {
      enhanced += ` Please structure your response with clear sections: 1) Overview, 2) Details, 3) Examples, 4) Summary.`;
    }
    
    if (techniques.includes('few_shot')) {
      enhanced += ` Here are some examples of what I'm looking for: Example 1: ... Example 2: ...`;
    }

    return enhanced;
  }

  /**
   * Generate multiple history items
   */
  static generateHistoryItems(count: number, options?: {
    userId?: string;
    dateRange?: { start: Date; end: Date };
    specificTechniques?: string[];
    specificIntents?: string[];
  }): any[] {
    const items = [];
    const now = new Date();
    const startDate = options?.dateRange?.start || new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000); // 30 days ago
    const endDate = options?.dateRange?.end || now;

    for (let i = 0; i < count; i++) {
      const originalPrompt = this.generatePrompt();
      const techniques = options?.specificTechniques || this.randomSubset(this.TECHNIQUES, 1, 3);
      const enhancedPrompt = this.generateEnhancedPrompt(originalPrompt, techniques);
      const intent = options?.specificIntents?.[0] || this.randomChoice(this.INTENTS);
      const complexity = this.randomChoice(this.COMPLEXITY_LEVELS);
      const confidence = Math.random() * 0.4 + 0.6; // 0.6 to 1.0
      
      // Generate random date within range
      const randomTime = startDate.getTime() + Math.random() * (endDate.getTime() - startDate.getTime());
      const createdAt = new Date(randomTime);

      items.push({
        id: `test-${Date.now()}-${i}`,
        user_id: options?.userId || 'test-user-id',
        original_input: originalPrompt,
        enhanced_output: enhancedPrompt,
        intent,
        complexity,
        techniques_used: techniques,
        confidence,
        created_at: createdAt.toISOString(),
        metadata: {
          test: true,
          generated: true,
          index: i
        }
      });
    }

    return items;
  }

  /**
   * Generate search test cases
   */
  static generateSearchTestCases(): Array<{
    query: string;
    expectedMatches: string[];
    description: string;
  }> {
    return [
      {
        query: 'fibonacci',
        expectedMatches: ['fibonacci numbers'],
        description: 'Search for specific programming term'
      },
      {
        query: 'API',
        expectedMatches: ['REST API', 'API endpoint'],
        description: 'Search for acronym'
      },
      {
        query: 'chain_of_thought',
        expectedMatches: ['chain_of_thought'],
        description: 'Search by technique name'
      },
      {
        query: 'analyze market',
        expectedMatches: ['Analyze the market trends'],
        description: 'Multi-word search'
      },
      {
        query: '@#$',
        expectedMatches: ['Special case test'],
        description: 'Special character search'
      }
    ];
  }

  /**
   * Generate pagination test scenarios
   */
  static generatePaginationScenarios(): Array<{
    totalItems: number;
    itemsPerPage: number;
    scenario: string;
    expectedPages: number;
  }> {
    return [
      {
        totalItems: 0,
        itemsPerPage: 10,
        scenario: 'Empty history',
        expectedPages: 0
      },
      {
        totalItems: 5,
        itemsPerPage: 10,
        scenario: 'Less than one page',
        expectedPages: 1
      },
      {
        totalItems: 10,
        itemsPerPage: 10,
        scenario: 'Exactly one page',
        expectedPages: 1
      },
      {
        totalItems: 25,
        itemsPerPage: 10,
        scenario: 'Multiple pages',
        expectedPages: 3
      },
      {
        totalItems: 100,
        itemsPerPage: 10,
        scenario: 'Many pages',
        expectedPages: 10
      },
      {
        totalItems: 1000,
        itemsPerPage: 10,
        scenario: 'Large dataset',
        expectedPages: 100
      }
    ];
  }

  // Helper methods
  private static randomChoice<T>(array: T[]): T {
    return array[Math.floor(Math.random() * array.length)];
  }

  private static randomSubset<T>(array: T[], min: number, max: number): T[] {
    const count = Math.floor(Math.random() * (max - min + 1)) + min;
    const shuffled = [...array].sort(() => 0.5 - Math.random());
    return shuffled.slice(0, count);
  }
}