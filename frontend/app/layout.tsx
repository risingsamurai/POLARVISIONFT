import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "POLARIS — Antarctic Navigation DSS",
  description:
    "AI-enabled Antarctic sea-ice, iceberg trajectory and navigation decision support",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
