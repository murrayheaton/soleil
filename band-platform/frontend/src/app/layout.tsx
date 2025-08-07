'use client';

import { usePathname } from "next/navigation";
import { Inter } from "next/font/google";
import "./globals.css";
import Layout from "@/components/Layout";
import { AuthProvider } from "@/contexts/AuthContext";

const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const pathname = usePathname();
  
  // Login page has its own layout
  const isLoginPage = pathname === '/login';
  
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <title>Band Platform</title>
        <meta name="description" content="A Progressive Web App for band management with Google Workspace integration" />
        <link rel="manifest" href="/manifest.json" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="Band Platform" />
        <meta name="format-detection" content="telephone=no" />
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
        <meta name="theme-color" content="#1f2937" />
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link rel="apple-touch-icon" href="/icons/icon-192x192.png" />
      </head>
      <body className={`${inter.className} antialiased`}>
        <AuthProvider>
          {isLoginPage ? children : <Layout>{children}</Layout>}
        </AuthProvider>
      </body>
    </html>
  );
}
