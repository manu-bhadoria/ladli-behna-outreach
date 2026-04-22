import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "लाड़ली बहना संवाद — मुख्यमंत्री मध्य प्रदेश",
  description:
    "मुख्यमंत्री डॉक्टर मोहन यादव की ओर से — लाड़ली बहना योजना लाभार्थियों से सीधा संवाद।",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="hi">
      <head>
        <link rel="preload" as="image" href="/ladli.jpg" fetchPriority="high" />
      </head>
      <body>{children}</body>
    </html>
  );
}
