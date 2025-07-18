'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { ArrowRight, Brain, Zap, Shield, Users, BarChart3, Sparkles } from 'lucide-react'
import Container from '@/components/layout/Container'

const features = [
  {
    icon: Brain,
    title: 'Intelligent Analysis',
    description: 'Our AI analyzes your input to understand intent, complexity, and optimal techniques.',
  },
  {
    icon: Zap,
    title: 'Instant Enhancement',
    description: 'Get enhanced prompts in seconds with state-of-the-art prompt engineering techniques.',
  },
  {
    icon: Shield,
    title: 'Enterprise Ready',
    description: 'Built with security, compliance, and scalability for enterprise deployments.',
  },
  {
    icon: Users,
    title: 'Team Collaboration',
    description: 'Share prompt libraries, templates, and best practices across your organization.',
  },
  {
    icon: BarChart3,
    title: 'Performance Tracking',
    description: 'Monitor effectiveness and continuously improve your prompt strategies.',
  },
  {
    icon: Sparkles,
    title: 'Always Learning',
    description: 'Our models continuously improve based on user feedback and latest research.',
  },
]

const techniques = [
  'Chain of Thought',
  'Tree of Thoughts',
  'Few-shot Learning',
  'Zero-shot CoT',
  'Self-Consistency',
  'Constitutional AI',
]

export default function Home() {
  return (
    <>
      {/* Hero Section */}
      <section className="relative overflow-hidden py-20 sm:py-32">
        <Container>
          <div className="mx-auto max-w-4xl text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <h1 className="mb-6 text-5xl font-bold tracking-tight sm:text-6xl md:text-7xl">
                Prompt Engineering
                <span className="block gradient-text">Made Simple</span>
              </h1>
              <p className="mx-auto mb-10 max-w-2xl text-lg text-gray-600 sm:text-xl">
                Transform your ideas into optimized prompts with AI-powered suggestions. 
                No expertise required - we handle the complexity for you.
              </p>
              <div className="flex flex-col gap-4 sm:flex-row sm:justify-center">
                <Link
                  href="/enhance"
                  className="btn-primary text-base px-8 py-3"
                >
                  Start Enhancing
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
                <Link
                  href="/docs"
                  className="btn-secondary text-base px-8 py-3"
                >
                  Learn More
                </Link>
              </div>
            </motion.div>

            {/* Technique Pills */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3, duration: 0.5 }}
              className="mt-16"
            >
              <p className="mb-4 text-sm font-medium text-gray-500">
                Powered by advanced techniques:
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {techniques.map((technique, index) => (
                  <motion.span
                    key={technique}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.4 + index * 0.05 }}
                    className="rounded-full bg-blue-50 px-4 py-2 text-sm font-medium text-blue-700"
                  >
                    {technique}
                  </motion.span>
                ))}
              </div>
            </motion.div>
          </div>
        </Container>

        {/* Background decoration */}
        <div className="absolute inset-0 -z-10 overflow-hidden">
          <div className="absolute left-[50%] top-0 h-[500px] w-[500px] -translate-x-[50%] rounded-full bg-gradient-to-br from-blue-100 to-purple-100 opacity-20 blur-3xl" />
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 sm:py-32">
        <Container>
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="mb-4 text-3xl font-bold sm:text-4xl">
              Everything You Need
            </h2>
            <p className="text-lg text-gray-600">
              Comprehensive tools and features to elevate your prompting game
            </p>
          </div>

          <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                viewport={{ once: true }}
                className="card group"
              >
                <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-blue-50 text-blue-600 transition-colors group-hover:bg-blue-100">
                  <feature.icon className="h-6 w-6" />
                </div>
                <h3 className="mb-2 text-xl font-semibold">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </Container>
      </section>

      {/* CTA Section */}
      <section className="py-20 sm:py-32">
        <Container>
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-blue-600 to-purple-600 px-8 py-16 text-center text-white sm:px-16 sm:py-20"
          >
            <h2 className="mb-4 text-3xl font-bold sm:text-4xl">
              Ready to Transform Your Prompts?
            </h2>
            <p className="mx-auto mb-8 max-w-2xl text-lg text-blue-100">
              Join thousands of users who are already creating better prompts with less effort.
            </p>
            <Link
              href="/enhance"
              className="inline-flex items-center rounded-lg bg-white px-8 py-3 text-base font-medium text-blue-600 transition-colors hover:bg-gray-100"
            >
              Get Started Free
              <ArrowRight className="ml-2 h-5 w-5" />
            </Link>

            {/* Background decoration */}
            <div className="absolute -right-20 -top-20 h-80 w-80 rounded-full bg-white/10 blur-3xl" />
            <div className="absolute -bottom-20 -left-20 h-80 w-80 rounded-full bg-white/10 blur-3xl" />
          </motion.div>
        </Container>
      </section>
    </>
  )
}