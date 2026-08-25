import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Everest · Summit Window",
  description: "Everest 3D digital twin — Summit Window decision support",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>): React.JSX.Element {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
