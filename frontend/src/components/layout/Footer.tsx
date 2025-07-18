import Link from 'next/link'
import { Sparkles } from 'lucide-react'
import Container from './Container'

const footerLinks = {
  Product: [
    { label: 'Features', href: '/features' },
    { label: 'Techniques', href: '/techniques' },
    { label: 'Pricing', href: '/pricing' },
    { label: 'Changelog', href: '/changelog' },
  ],
  Resources: [
    { label: 'Documentation', href: '/docs' },
    { label: 'API Reference', href: '/api' },
    { label: 'Blog', href: '/blog' },
    { label: 'Community', href: '/community' },
  ],
  Company: [
    { label: 'About', href: '/about' },
    { label: 'Careers', href: '/careers' },
    { label: 'Privacy', href: '/privacy' },
    { label: 'Terms', href: '/terms' },
  ],
  Connect: [
    { label: 'Twitter', href: 'https://twitter.com' },
    { label: 'GitHub', href: 'https://github.com' },
    { label: 'Discord', href: 'https://discord.com' },
    { label: 'Contact', href: '/contact' },
  ],
}

export default function Footer() {
  return (
    <footer className="mt-auto border-t bg-gray-50">
      <Container>
        <div className="py-12">
          {/* Footer content grid */}
          <div className="grid grid-cols-2 gap-8 md:grid-cols-5">
            {/* Brand section */}
            <div className="col-span-2 md:col-span-1">
              <Link 
                href="/" 
                className="flex items-center gap-2 text-xl font-bold text-gray-900"
              >
                <Sparkles className="h-6 w-6" />
                <span>BetterPrompts</span>
              </Link>
              <p className="mt-4 text-sm text-gray-600">
                Making advanced prompt engineering accessible to everyone.
              </p>
            </div>

            {/* Links sections */}
            {Object.entries(footerLinks).map(([title, links]) => (
              <div key={title}>
                <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
                <ul className="mt-4 space-y-3">
                  {links.map((link) => (
                    <li key={link.href}>
                      <Link
                        href={link.href}
                        className="text-sm text-gray-600 transition-colors hover:text-gray-900"
                        {...(link.href.startsWith('http') && {
                          target: '_blank',
                          rel: 'noopener noreferrer',
                        })}
                      >
                        {link.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          {/* Bottom section */}
          <div className="mt-12 border-t pt-8">
            <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
              <p className="text-sm text-gray-600">
                © {new Date().getFullYear()} BetterPrompts. All rights reserved.
              </p>
              <div className="flex gap-6">
                <Link
                  href="/privacy"
                  className="text-sm text-gray-600 transition-colors hover:text-gray-900"
                >
                  Privacy Policy
                </Link>
                <Link
                  href="/terms"
                  className="text-sm text-gray-600 transition-colors hover:text-gray-900"
                >
                  Terms of Service
                </Link>
              </div>
            </div>
          </div>
        </div>
      </Container>
    </footer>
  )
}