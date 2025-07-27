/**
 * Prompt Test Data Fixtures
 * Categorized by persona and use case
 */

export interface TestPrompt {
  id: string;
  text: string;
  persona: string;
  category: string;
  expectedTechniques?: string[];
  complexity: 'simple' | 'moderate' | 'complex';
}

export const testPrompts: Record<string, TestPrompt> = {
  // Sarah - Marketing Manager Prompts
  sarahSimple: {
    id: 'sarah-simple-1',
    text: 'Write a social media post about our new product launch',
    persona: 'sarah',
    category: 'marketing',
    expectedTechniques: ['audience_targeting', 'emotional_appeal'],
    complexity: 'simple',
  },
  
  sarahModerate: {
    id: 'sarah-moderate-1',
    text: 'Create a comprehensive email campaign for our quarterly sale with personalization strategies',
    persona: 'sarah',
    category: 'marketing',
    expectedTechniques: ['personalization', 'segmentation', 'call_to_action'],
    complexity: 'moderate',
  },
  
  sarahComplex: {
    id: 'sarah-complex-1',
    text: 'Develop a multi-channel marketing strategy for launching our product in three new international markets, considering cultural differences and local regulations',
    persona: 'sarah',
    category: 'marketing',
    expectedTechniques: ['market_analysis', 'cultural_adaptation', 'regulatory_compliance'],
    complexity: 'complex',
  },
  
  // Alex - Developer Prompts
  alexSimple: {
    id: 'alex-simple-1',
    text: 'Write a function to validate email addresses',
    persona: 'alex',
    category: 'code',
    expectedTechniques: ['code_structure', 'input_validation'],
    complexity: 'simple',
  },
  
  alexModerate: {
    id: 'alex-moderate-1',
    text: 'Design a REST API for a user authentication system with JWT tokens',
    persona: 'alex',
    category: 'code',
    expectedTechniques: ['api_design', 'security_patterns', 'documentation'],
    complexity: 'moderate',
  },
  
  alexComplex: {
    id: 'alex-complex-1',
    text: 'Architect a microservices solution for an e-commerce platform handling 10,000 concurrent users with real-time inventory updates',
    persona: 'alex',
    category: 'code',
    expectedTechniques: ['system_design', 'scalability', 'real_time_systems'],
    complexity: 'complex',
  },
  
  // Dr. Chen - Data Scientist Prompts
  chenSimple: {
    id: 'chen-simple-1',
    text: 'Explain the concept of linear regression to a non-technical audience',
    persona: 'chen',
    category: 'data_science',
    expectedTechniques: ['simplification', 'analogies'],
    complexity: 'simple',
  },
  
  chenModerate: {
    id: 'chen-moderate-1',
    text: 'Design an experiment to test the effectiveness of a new recommendation algorithm',
    persona: 'chen',
    category: 'data_science',
    expectedTechniques: ['experimental_design', 'statistical_analysis', 'metrics_definition'],
    complexity: 'moderate',
  },
  
  chenComplex: {
    id: 'chen-complex-1',
    text: 'Develop a machine learning pipeline for fraud detection that handles imbalanced datasets, explains predictions, and meets regulatory requirements',
    persona: 'chen',
    category: 'data_science',
    expectedTechniques: ['ml_pipeline', 'explainability', 'compliance', 'imbalanced_data'],
    complexity: 'complex',
  },
  
  // Maria - Content Creator Prompts
  mariaSimple: {
    id: 'maria-simple-1',
    text: 'Write an engaging Instagram caption for a travel photo',
    persona: 'maria',
    category: 'content',
    expectedTechniques: ['engagement_hooks', 'hashtag_strategy'],
    complexity: 'simple',
  },
  
  mariaModerate: {
    id: 'maria-moderate-1',
    text: 'Create a content calendar for a lifestyle blog covering wellness, fashion, and travel',
    persona: 'maria',
    category: 'content',
    expectedTechniques: ['content_planning', 'topic_clustering', 'seasonal_relevance'],
    complexity: 'moderate',
  },
  
  mariaComplex: {
    id: 'maria-complex-1',
    text: 'Develop a comprehensive content strategy for a brand transformation, including voice guidelines, content pillars, and multi-platform distribution',
    persona: 'maria',
    category: 'content',
    expectedTechniques: ['brand_voice', 'content_strategy', 'multi_channel', 'audience_mapping'],
    complexity: 'complex',
  },
  
  // TechCorp - Enterprise Prompts
  techcorpSimple: {
    id: 'techcorp-simple-1',
    text: 'Generate a security policy template for remote work',
    persona: 'techcorp',
    category: 'enterprise',
    expectedTechniques: ['policy_structure', 'compliance_language'],
    complexity: 'simple',
  },
  
  techcorpModerate: {
    id: 'techcorp-moderate-1',
    text: 'Design a data governance framework for a multinational corporation with GDPR and CCPA compliance',
    persona: 'techcorp',
    category: 'enterprise',
    expectedTechniques: ['governance_framework', 'regulatory_compliance', 'process_design'],
    complexity: 'moderate',
  },
  
  techcorpComplex: {
    id: 'techcorp-complex-1',
    text: 'Create an enterprise-wide digital transformation roadmap including cloud migration, process automation, and change management strategies',
    persona: 'techcorp',
    category: 'enterprise',
    expectedTechniques: ['strategic_planning', 'change_management', 'technical_architecture', 'risk_assessment'],
    complexity: 'complex',
  },
  
  // Edge Cases and Special Prompts
  veryShort: {
    id: 'edge-short-1',
    text: 'Hi',
    persona: 'sarah',
    category: 'edge_case',
    complexity: 'simple',
  },
  
  veryLong: {
    id: 'edge-long-1',
    text: 'Lorem ipsum dolor sit amet, '.repeat(500), // ~3000 characters
    persona: 'alex',
    category: 'edge_case',
    complexity: 'complex',
  },
  
  multiLanguage: {
    id: 'edge-multilang-1',
    text: 'Create a greeting that says "Hello" in English, "Bonjour" in French, and "你好" in Chinese',
    persona: 'maria',
    category: 'edge_case',
    expectedTechniques: ['multilingual', 'cultural_awareness'],
    complexity: 'simple',
  },
  
  maliciousAttempt: {
    id: 'edge-malicious-1',
    text: "'; DROP TABLE users; -- Write a story",
    persona: 'alex',
    category: 'security_test',
    complexity: 'simple',
  },
};

/**
 * Get prompts by persona
 */
export function getPromptsByPersona(persona: string): TestPrompt[] {
  return Object.values(testPrompts).filter(prompt => prompt.persona === persona);
}

/**
 * Get prompts by complexity
 */
export function getPromptsByComplexity(complexity: string): TestPrompt[] {
  return Object.values(testPrompts).filter(prompt => prompt.complexity === complexity);
}

/**
 * Get random prompt
 */
export function getRandomPrompt(): TestPrompt {
  const prompts = Object.values(testPrompts);
  return prompts[Math.floor(Math.random() * prompts.length)];
}

/**
 * Generate batch of prompts for testing
 */
export function generatePromptBatch(count: number, persona: string): TestPrompt[] {
  const basePrompts = getPromptsByPersona(persona);
  const batch: TestPrompt[] = [];
  
  for (let i = 0; i < count; i++) {
    const basePrompt = basePrompts[i % basePrompts.length];
    batch.push({
      ...basePrompt,
      id: `${basePrompt.id}-batch-${i}`,
      text: `${basePrompt.text} (Batch item ${i + 1})`,
    });
  }
  
  return batch;
}