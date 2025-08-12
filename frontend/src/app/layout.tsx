import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Lawyerless - Análise de Contratos de Investimento',
  description: 'Análise inteligente de contratos de investimento com IA. Identifique riscos, entenda cláusulas e tome decisões informadas.',
  keywords: ['contratos', 'investimento', 'análise jurídica', 'IA', 'SAFE', 'term sheet', 'due diligence'],
  authors: [{ name: 'Equipe Lawyerless' }],
  creator: 'Lawyerless',
  publisher: 'Lawyerless',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'),
  openGraph: {
    title: 'Lawyerless - Análise de Contratos de Investimento',
    description: 'Análise inteligente de contratos de investimento com IA',
    url: '/',
    siteName: 'Lawyerless',
    images: [
      {
        url: '/og-image.jpg',
        width: 1200,
        height: 630,
        alt: 'Lawyerless - Análise de Contratos de Investimento',
      },
    ],
    locale: 'pt_BR',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Lawyerless - Análise de Contratos de Investimento',
    description: 'Análise inteligente de contratos de investimento com IA',
    images: ['/og-image.jpg'],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  verification: {
    google: process.env.GOOGLE_VERIFICATION_ID,
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-BR" className="h-full">
      <head>
        {/* Preload critical resources */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        
        {/* PDF.js worker preload */}
        <link 
          rel="preload" 
          href="/pdf-worker.js" 
          as="script" 
          crossOrigin=""
        />
        
        {/* Favicon and app icons */}
        <link rel="icon" type="image/x-icon" href="/favicon.ico" />
        <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png" />
        <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
        <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
        <link rel="manifest" href="/site.webmanifest" />
        
        {/* Theme color for mobile browsers */}
        <meta name="theme-color" content="#0ea5e9" />
        <meta name="msapplication-TileColor" content="#0ea5e9" />
        
        {/* Prevent zoom on iOS */}
        <meta 
          name="viewport" 
          content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no"
        />
      </head>
      <body className={`${inter.className} h-full bg-gray-50 text-gray-900 antialiased`}>
        {/* Skip to main content for accessibility */}
        <a 
          href="#main-content" 
          className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 bg-primary-600 text-white px-4 py-2 rounded-md z-50"
        >
          Pular para o conteúdo principal
        </a>

        {/* Main application content */}
        <div id="main-content" className="h-full">
          {children}
        </div>

        {/* Global scripts */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              // Prevent FOUC (Flash of Unstyled Content)
              document.documentElement.style.visibility = 'visible';
              
              // Initialize theme based on user preference
              (function() {
                const theme = localStorage.getItem('theme') || 'light';
                if (theme === 'dark') {
                  document.documentElement.classList.add('dark');
                }
              })();
              
              // Error boundary for uncaught errors
              window.addEventListener('error', function(event) {
                console.error('Global error:', event.error);
                // You can send this to an error reporting service
              });
              
              window.addEventListener('unhandledrejection', function(event) {
                console.error('Unhandled promise rejection:', event.reason);
                // You can send this to an error reporting service
              });
            `,
          }}
        />
      </body>
    </html>
  )
}