/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  images: {
    unoptimized: true,
  },
  eslint: {
    // Warning: This allows production builds to successfully complete even if
    // your project has ESLint errors.
    ignoreDuringBuilds: true,
  },
  // Override webpack config
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // Disable static page exports during build
      config.optimization.minimize = true;
    }
    return config;
  },
};

module.exports = nextConfig;
