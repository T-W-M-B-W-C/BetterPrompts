/**
 * Test Data for US-001: Anonymous Prompt Enhancement Flow
 * 10 sample prompts covering various use cases and edge cases
 */

export interface AnonymousTestPrompt {
  id: string;
  description: string;
  text: string;
  expectedBehavior: string;
  category: 'valid' | 'edge' | 'boundary';
  expectedTechniques?: string[];
}

export const anonymousTestPrompts: AnonymousTestPrompt[] = [
  // Valid prompts
  {
    id: 'anon-valid-1',
    description: 'Simple question prompt',
    text: 'How do I improve my writing skills?',
    expectedBehavior: 'Should enhance with learning-focused techniques',
    category: 'valid',
    expectedTechniques: ['step_by_step', 'examples']
  },
  {
    id: 'anon-valid-2',
    description: 'Creative writing prompt',
    text: 'Write a short story about a time traveler who can only go backwards one hour at a time',
    expectedBehavior: 'Should enhance with creative writing techniques',
    category: 'valid',
    expectedTechniques: ['creative_constraints', 'narrative_structure']
  },
  {
    id: 'anon-valid-3',
    description: 'Business email prompt',
    text: 'Help me write an email to my boss requesting time off next month',
    expectedBehavior: 'Should enhance with professional communication techniques',
    category: 'valid',
    expectedTechniques: ['professional_tone', 'clear_structure']
  },
  {
    id: 'anon-valid-4',
    description: 'Technical explanation prompt',
    text: 'Explain how blockchain technology works to someone with no technical background',
    expectedBehavior: 'Should enhance with simplification and analogy techniques',
    category: 'valid',
    expectedTechniques: ['simplification', 'analogies', 'examples']
  },
  {
    id: 'anon-valid-5',
    description: 'Problem-solving prompt',
    text: 'I need to organize a virtual team building event for 50 remote employees',
    expectedBehavior: 'Should enhance with planning and organization techniques',
    category: 'valid',
    expectedTechniques: ['brainstorming', 'structured_planning', 'considerations']
  },

  // Edge cases
  {
    id: 'anon-edge-1',
    description: 'Very short prompt',
    text: 'Help',
    expectedBehavior: 'Should handle gracefully and suggest clarification',
    category: 'edge'
  },
  {
    id: 'anon-edge-2',
    description: 'Prompt with special characters',
    text: 'Create a regex pattern to match email addresses like user@example.com',
    expectedBehavior: 'Should handle special characters correctly',
    category: 'edge',
    expectedTechniques: ['technical_precision', 'examples']
  },
  {
    id: 'anon-edge-3',
    description: 'Multi-language prompt',
    text: 'Translate "Hello, how are you?" to Spanish, French, and German',
    expectedBehavior: 'Should enhance with language-specific techniques',
    category: 'edge',
    expectedTechniques: ['multilingual', 'cultural_context']
  },

  // Boundary cases
  {
    id: 'anon-boundary-1',
    description: 'Near character limit prompt (1990 chars)',
    text: 'I am working on a comprehensive research project about climate change and its impact on global food security. The project needs to cover multiple aspects including: 1) Historical climate data analysis from the past 50 years, 2) Current agricultural practices and their sustainability, 3) Projected climate scenarios for the next 30 years, 4) Potential adaptation strategies for farmers, 5) Economic implications for different regions, 6) Policy recommendations for governments, 7) Role of technology in mitigation efforts. ' + 
          'I need to structure this into a compelling presentation for both scientific and non-scientific audiences. The presentation should be engaging, data-driven, and actionable. It should include visual elements, clear narratives, and specific case studies from at least 5 different countries representing various climates and economic conditions. ' +
          'Additionally, I want to address common misconceptions about climate change and provide evidence-based counterarguments. The presentation should also include interactive elements to engage the audience and make the data more relatable. ' +
          'Can you help me create a comprehensive outline that addresses all these points while maintaining a logical flow and ensuring that each section builds upon the previous one? I also need suggestions for impactful opening and closing statements that will resonate with diverse audiences. ' +
          'The outline should be detailed enough to guide content creation but flexible enough to adapt based on audience feedback. Please include recommendations for data visualization techniques and tools that would be most effective for conveying complex climate data in an accessible manner. Also suggest ways to incorporate personal stories or testimonials that humanize the data without compromising scientific rigor.',
    expectedBehavior: 'Should handle long prompt successfully within limit',
    category: 'boundary',
    expectedTechniques: ['structured_organization', 'audience_adaptation', 'data_presentation']
  },
  {
    id: 'anon-boundary-2',
    description: 'Empty prompt',
    text: '',
    expectedBehavior: 'Should show validation error for empty prompt',
    category: 'boundary'
  }
];

/**
 * Get test prompts by category
 */
export function getPromptsByCategory(category: 'valid' | 'edge' | 'boundary'): AnonymousTestPrompt[] {
  return anonymousTestPrompts.filter(prompt => prompt.category === category);
}

/**
 * Get a random valid prompt
 */
export function getRandomValidPrompt(): AnonymousTestPrompt {
  const validPrompts = getPromptsByCategory('valid');
  return validPrompts[Math.floor(Math.random() * validPrompts.length)];
}

/**
 * Get prompt that should exceed character limit (for testing)
 */
export function getExceedingLimitPrompt(): string {
  return 'x'.repeat(2001); // 2001 characters to exceed 2000 limit
}

/**
 * Performance test scenarios
 */
export const performanceScenarios = [
  {
    name: 'Simple prompt enhancement',
    prompt: anonymousTestPrompts[0], // Simple question
    expectedMaxTime: 2000 // 2 seconds
  },
  {
    name: 'Complex prompt enhancement',
    prompt: anonymousTestPrompts[8], // Near character limit
    expectedMaxTime: 2000 // 2 seconds even for complex
  },
  {
    name: 'Rapid sequential enhancements',
    prompts: getPromptsByCategory('valid').slice(0, 3),
    expectedMaxTimeEach: 3000 // Allow more time for full enhancement flow including text entry
  }
];