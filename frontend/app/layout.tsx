import type { Metadata, Viewport } from "next";
import { Baloo_2, Hind } from "next/font/google";
import "./globals.css";

const baloo = Baloo_2({ variable: "--font-baloo", subsets: ["latin", "devanagari"], weight: ["600", "700"] });
const hind = Hind({ variable: "--font-hind", subsets: ["latin", "devanagari"], weight: ["400", "500", "600"] });

export const metadata: Metadata = {
  title: "Airtel Udyam",
  description: "Get the right internet, phone and digital tools for your business in one sitting.",
};

export const viewport: Viewport = { themeColor: "#e40000", width: "device-width", initialScale: 1 };

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${baloo.variable} ${hind.variable} h-full antialiased`}>
      <body className="min-h-full font-sans">{children}</body>
    </html>
  );
}
