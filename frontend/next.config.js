/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable experimental features for better PDF.js integration
  experimental: {
    serverComponentsExternalPackages: ['pdfjs-dist']
  },

  // Webpack configuration for PDF.js
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // PDF.js worker configuration
    config.resolve.alias = {
      ...config.resolve.alias,
      // Map PDF.js worker to the correct path
      'pdfjs-dist/build/pdf.worker.js': 'pdfjs-dist/build/pdf.worker.mjs'
    }

    // Handle PDF.js worker files
    config.module.rules.push({
      test: /pdf\.worker\.(min\.)?js/,
      type: 'asset/resource',
      generator: {
        filename: 'static/worker/[hash][ext][query]'
      }
    })

    // Ignore canvas for PDF.js (use DOM rendering instead)
    config.resolve.alias.canvas = false

    // Ensure proper handling of ES modules
    config.experiments = {
      ...config.experiments,
      topLevelAwait: true
    }

    return config
  },

  // Headers configuration for CORS and security
  async headers() {
    return [
      {
        // Match all routes
        source: '/(.*)',
        headers: [
          // CORS headers for backend communication
          {
            key: 'Access-Control-Allow-Origin',
            value: process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
          },
          {
            key: 'Access-Control-Allow-Methods', 
            value: 'GET, POST, PUT, DELETE, OPTIONS'
          },
          {
            key: 'Access-Control-Allow-Headers',
            value: 'Content-Type, Authorization'
          },
          // Security headers
          {
            key: 'X-Frame-Options',
            value: 'DENY'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin'
          }
        ]
      },
      {
        // Special headers for PDF.js worker files
        source: '/pdf-worker.js',
        headers: [
          {
            key: 'Content-Type',
            value: 'application/javascript'
          },
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable'
          }
        ]
      }
    ]
  },

  // Rewrites for API proxy (optional)
  async rewrites() {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    
    return [
      {
        source: '/api/backend/:path*',
        destination: `${backendUrl}/api/v1/:path*`
      }
    ]
  },

  // Environment variables validation
  env: {
    NEXT_PUBLIC_BACKEND_URL: process.env.NEXT_PUBLIC_BACKEND_URL,
    NEXT_PUBLIC_APP_VERSION: process.env.npm_package_version || '1.0.0'
  },

  // Image optimization
  images: {
    domains: []
  },

  // Compiler options
  compiler: {
    // Remove console logs in production
    removeConsole: process.env.NODE_ENV === 'production'
  },

  // Output configuration
  output: 'standalone',

  // TypeScript configuration
  typescript: {
    // Ignore TypeScript errors during build (handle via separate type-check)
    ignoreBuildErrors: false
  },

  // ESLint configuration
  eslint: {
    ignoreDuringBuilds: false
  },

  // Redirect configuration
  async redirects() {
    return []
  },

  // Static file serving
  trailingSlash: false,

  // React strict mode
  reactStrictMode: true,

  // SWC minification
  swcMinify: true
}

module.exports = nextConfig