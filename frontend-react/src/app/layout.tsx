import type { Metadata } from "next";
import { Roboto } from "next/font/google";
import "./globals.css";
import ThemeProvider from "@/components/ThemeProvider";
import ReduxProvider from "@/components/ReduxProvider";
import AuthInitializer from "@/components/AuthInitializer";
import ErrorBoundary from "@/components/ErrorBoundary";

const roboto = Roboto({
  weight: ['300', '400', '500', '700'],
  subsets: ['latin'],
  display: 'swap',
});

export const metadata: Metadata = {
  title: "Infra Mind - AI Infrastructure Advisory Platform",
  description: "Intelligent AI-powered advisory platform for strategic AI infrastructure planning, compliance, and scaling recommendations.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={roboto.className}>
        <ReduxProvider>
          <ThemeProvider>
            <ErrorBoundary>
              <AuthInitializer />
              {children}
            </ErrorBoundary>
          </ThemeProvider>
        </ReduxProvider>
      </body>
    </html>
  );
}
