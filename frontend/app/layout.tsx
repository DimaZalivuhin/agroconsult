import type { Metadata } from "next";

import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import { ToastProvider } from "@/components/ui/toast";

export const metadata: Metadata = {
  title: "AgroConsult — консультант по господдержке АПК",
  description:
    "Сервис для крестьянских и фермерских хозяйств: ответы на вопросы о грантах, субсидиях и льготах со ссылками на нормативные акты.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" suppressHydrationWarning>
      <body className="font-sans antialiased">
        <ToastProvider>
          <AuthProvider>{children}</AuthProvider>
        </ToastProvider>
      </body>
    </html>
  );
}
