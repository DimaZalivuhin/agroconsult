"use client";

import { useRouter, usePathname } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { useAuth } from "@/lib/auth-context";

export function RequireAuth({
  children,
  adminOnly = false,
}: {
  children: ReactNode;
  adminOnly?: boolean;
}) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (loading) return;
    if (!user) {
      const target = encodeURIComponent(pathname || "/dashboard");
      router.replace(`/login?next=${target}`);
      return;
    }
    if (adminOnly && user.role !== "admin") {
      router.replace("/dashboard");
    }
  }, [user, loading, router, adminOnly, pathname]);

  if (loading || !user || (adminOnly && user.role !== "admin")) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-muted-foreground text-sm">Загрузка…</div>
      </div>
    );
  }

  return <>{children}</>;
}
