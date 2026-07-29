import type { Metadata } from "next";
import { Cormorant_Garamond, Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const cormorant = Cormorant_Garamond({
  variable: "--font-editorial",
  subsets: ["latin"],
  weight: ["500", "600", "700"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://arxiv-recsys.openai.site"),
  title: {
    default: "Aster — Research discovery, made deliberate",
    template: "%s · Aster",
  },
  description:
    "A citation-aware search and recommendation workspace for arXiv research.",
  openGraph: {
    title: "Aster — Research discovery, made deliberate",
    description:
      "Search, rank, and organize the literature frontier with transparent recommendations.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Aster — Research discovery, made deliberate",
    description:
      "Search, rank, and organize the literature frontier with transparent recommendations.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} ${cormorant.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
