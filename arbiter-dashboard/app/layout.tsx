import type { Metadata } from "next";
import { Providers } from "@/components/providers";
import { CustomCursor } from "@/components/cursor";

import "@fontsource/jetbrains-mono/400.css";
import "@fontsource/jetbrains-mono/500.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "Arbiter",
  description: "Observability for data pipelines",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <body>
        <Providers>{children}</Providers>
        <CustomCursor />
      </body>
    </html>
  );
}
