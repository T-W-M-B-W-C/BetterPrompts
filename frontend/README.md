# BetterPrompts Frontend

Modern web application for AI-powered prompt engineering assistance.

## Tech Stack

- **Framework**: Next.js 14+ with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Animations**: Framer Motion
- **UI Components**: Radix UI
- **Icons**: Lucide React
- **API Client**: Axios

## Getting Started

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Project Structure

```
src/
├── app/                    # Next.js app router pages
│   ├── enhance/           # Prompt enhancement page
│   └── page.tsx           # Home page
├── components/            # React components
│   ├── enhance/          # Enhancement-specific components
│   ├── layout/           # Layout components (Header, Footer)
│   └── providers/        # Context providers
├── hooks/                 # Custom React hooks
├── lib/                   # Utilities and libraries
│   └── api/              # API integration layer
├── store/                 # Zustand state management
└── types/                 # TypeScript type definitions
```

## Key Features

- 🎨 Modern, responsive UI with Tailwind CSS
- ♿ Full accessibility support with WCAG 2.1 AA compliance
- 🚀 Optimized performance with Next.js 14+
- 🔐 Secure authentication flow
- 📱 Mobile-first design
- 🌐 API integration ready
- 🧠 Smart state management with Zustand
- ✨ Smooth animations with Framer Motion

## Accessibility Features

- Skip to content link
- Keyboard navigation indicators
- Screen reader announcements
- Focus trap for modals
- Reduced motion support
- High contrast mode support
- ARIA labels and landmarks

## Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Development Notes

- The app uses Next.js App Router for routing
- All components are TypeScript-enabled
- Tailwind CSS is configured with custom utilities
- API integration is prepared but backend is not yet implemented
- Mock data is used for techniques and enhancements

## Available Routes

- `/` - Landing page with features overview
- `/enhance` - Main prompt enhancement interface
- `/techniques` - Browse available techniques (coming soon)
- `/dashboard` - User dashboard (coming soon)
- `/docs` - Documentation (coming soon)

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme).

Check out the [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.