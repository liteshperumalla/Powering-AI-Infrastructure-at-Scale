import type { Metadata } from "next";
import { Roboto } from "next/font/google";
import "./globals.css";
import ThemeProvider from "@/components/ThemeProvider";
import ReduxProvider from "@/components/ReduxProvider";
import AuthInitializer from "@/components/AuthInitializer";
import ErrorBoundary from "@/components/ErrorBoundary";
import GoogleOAuthProvider from "@/components/GoogleOAuthProvider";

const roboto = Roboto({
  weight: ['300', '400', '500', '700'],
  subsets: ['latin'],
  display: 'swap',
});

export const metadata: Metadata = {
  title: "Infra Mind - AI Infrastructure Advisory Platform",
  description: "Intelligent AI-powered advisory platform for strategic AI infrastructure planning, compliance, and scaling recommendations.",
  icons: {
    icon: [
      { url: '/favicon.svg', type: 'image/svg+xml' },
      { url: '/infra-mind-icon.svg', type: 'image/svg+xml', sizes: 'any' }
    ],
    shortcut: '/favicon.svg',
    apple: '/infra-mind-icon.svg',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-scroll-behavior="smooth" suppressHydrationWarning>
      <body className={roboto.className} suppressHydrationWarning>
        <ReduxProvider>
          <GoogleOAuthProvider>
            <ThemeProvider>
              <ErrorBoundary>
                <AuthInitializer />
                {children}
              </ErrorBoundary>
            </ThemeProvider>
          </GoogleOAuthProvider>
        </ReduxProvider>
      </body>
    </html>
  );
}
