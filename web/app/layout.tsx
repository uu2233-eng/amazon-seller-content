import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/sidebar";

export const metadata: Metadata = {
  title: "Amazon Seller Content Engine",
  description: "热点内容抓取 & AI 内容创意生成引擎",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <Sidebar />
        <main className="ml-64 min-h-screen">
          <div className="mx-auto max-w-7xl px-6 py-8">{children}</div>
        </main>
      </body>
    </html>
  );
}
