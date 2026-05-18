"use client";

import { Menu, Sprout } from "lucide-react";
import Link from "next/link";

import { RequireAuth } from "@/components/require-auth";
import { Sidebar } from "@/components/sidebar";
import { Button } from "@/components/ui/button";
import { MobileNavProvider, useMobileNav } from "@/lib/mobile-nav-context";

/**
 * Mobile-only top header with hamburger + brand. Hidden on md+ screens, where
 * the sidebar itself acts as the navigation surface.
 */
function MobileHeader() {
  const { toggle } = useMobileNav();
  return (
    <header className="md:hidden sticky top-0 z-30 h-14 border-b bg-background flex items-center justify-between px-3">
      <Button
        variant="ghost"
        size="icon"
        onClick={toggle}
        aria-label="Открыть меню"
      >
        <Menu className="h-5 w-5" />
      </Button>
      <Link href="/dashboard" className="flex items-center gap-2">
        <Sprout className="h-5 w-5 text-primary" />
        <span className="font-medium">AgroConsult</span>
      </Link>
      {/* Spacer keeps the brand visually centred without measuring widths. */}
      <div className="w-9" aria-hidden="true" />
    </header>
  );
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth>
      <MobileNavProvider>
        <div className="flex min-h-screen">
          <Sidebar />
          <div className="flex-1 min-w-0 flex flex-col">
            <MobileHeader />
            <main className="flex-1 min-w-0">{children}</main>
          </div>
        </div>
      </MobileNavProvider>
    </RequireAuth>
  );
}
