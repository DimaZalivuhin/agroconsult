"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  FileText,
  LayoutDashboard,
  LogOut,
  MessageSquarePlus,
  Plus,
  Settings,
  ShieldCheck,
  Sprout,
  Trash2,
  UserCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { chat } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { ChatSession } from "@/lib/types";
import { cn } from "@/lib/utils";

interface Group {
  label: string;
  items: ChatSession[];
}

function groupSessions(items: ChatSession[]): Group[] {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const weekAgo = new Date(today);
  weekAgo.setDate(weekAgo.getDate() - 7);

  const buckets: Record<string, ChatSession[]> = {
    Сегодня: [],
    Вчера: [],
    "Последние 7 дней": [],
    Ранее: [],
  };

  for (const s of items) {
    const d = new Date(s.updated_at);
    if (d >= today) buckets["Сегодня"].push(s);
    else if (d >= yesterday) buckets["Вчера"].push(s);
    else if (d >= weekAgo) buckets["Последние 7 дней"].push(s);
    else buckets["Ранее"].push(s);
  }

  return Object.entries(buckets)
    .filter(([, arr]) => arr.length > 0)
    .map(([label, arr]) => ({ label, items: arr }));
}

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const { toast } = useToast();

  const [sessions, setSessions] = useState<ChatSession[] | null>(null);
  const [loading, setLoading] = useState(true);

  async function loadSessions() {
    try {
      const data = await chat.sessions();
      setSessions(data.items);
    } catch {
      setSessions([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSessions();
    // Refresh every 30 seconds while sidebar is mounted
    const interval = setInterval(loadSessions, 30000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname]);

  async function handleDelete(id: string, e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm("Удалить эту консультацию?")) return;
    try {
      await chat.deleteSession(id);
      setSessions((prev) => prev?.filter((s) => s.id !== id) ?? null);
      if (pathname === `/chat/${id}`) router.push("/chat");
      toast({ title: "Консультация удалена" });
    } catch {
      toast({ title: "Не удалось удалить", variant: "destructive" });
    }
  }

  const groups = sessions ? groupSessions(sessions) : [];
  const isAdmin = user?.role === "admin";

  return (
    <aside className="w-72 shrink-0 h-screen sticky top-0 border-r bg-muted/30 flex flex-col">
      {/* Logo */}
      <div className="h-14 px-4 flex items-center border-b shrink-0">
        <Link href="/dashboard" className="flex items-center gap-2">
          <Sprout className="h-5 w-5 text-primary" />
          <span className="font-medium">AgroConsult</span>
        </Link>
      </div>

      {/* New chat */}
      <div className="p-3 shrink-0">
        <Link href="/chat">
          <Button variant="outline" className="w-full justify-start gap-2 h-10">
            <MessageSquarePlus className="h-4 w-4" />
            Новая консультация
          </Button>
        </Link>
      </div>

      {/* Sessions list */}
      <div className="flex-1 overflow-y-auto px-2 pb-2">
        {loading && (
          <div className="space-y-2 px-2 py-2">
            <Skeleton className="h-7 w-full" />
            <Skeleton className="h-7 w-full" />
            <Skeleton className="h-7 w-full" />
          </div>
        )}
        {!loading && groups.length === 0 && (
          <div className="px-3 py-6 text-xs text-muted-foreground text-center">
            История консультаций появится здесь
          </div>
        )}
        {groups.map((group) => (
          <div key={group.label} className="mb-4">
            <div className="text-xs text-muted-foreground px-2 py-1 font-medium uppercase tracking-wide">
              {group.label}
            </div>
            <div className="space-y-0.5">
              {group.items.map((s) => {
                const active = pathname === `/chat/${s.id}`;
                return (
                  <Link
                    key={s.id}
                    href={`/chat/${s.id}`}
                    className={cn(
                      "group flex items-center justify-between gap-2 rounded-md px-2 py-1.5 text-sm",
                      "hover:bg-accent transition-colors",
                      active && "bg-accent text-accent-foreground",
                    )}
                  >
                    <span className="truncate flex-1">{s.title || "Без названия"}</span>
                    <button
                      onClick={(e) => handleDelete(s.id, e)}
                      className="opacity-0 group-hover:opacity-100 transition-opacity p-0.5 rounded hover:bg-background"
                      title="Удалить"
                    >
                      <Trash2 className="h-3.5 w-3.5 text-muted-foreground" />
                    </button>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Bottom nav */}
      <div className="border-t p-2 shrink-0 space-y-0.5">
        <NavLink href="/dashboard" icon={<LayoutDashboard className="h-4 w-4" />}>
          Дашборд
        </NavLink>
        <NavLink href="/documents" icon={<FileText className="h-4 w-4" />}>
          База документов
        </NavLink>
        <NavLink href="/profile" icon={<UserCircle className="h-4 w-4" />}>
          Мой профиль
        </NavLink>
        {isAdmin && (
          <NavLink href="/admin" icon={<ShieldCheck className="h-4 w-4" />}>
            Админ-панель
          </NavLink>
        )}

        <div className="pt-2 mt-2 border-t flex items-center justify-between gap-2">
          <div className="flex-1 min-w-0 px-2">
            <div className="text-sm truncate">{user?.full_name || user?.email}</div>
            <div className="text-xs text-muted-foreground truncate">
              {isAdmin ? "Администратор" : "Фермер"}
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={logout}
            title="Выйти"
            className="shrink-0"
          >
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </aside>
  );
}

function NavLink({
  href,
  icon,
  children,
}: {
  href: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const active = pathname === href || pathname?.startsWith(`${href}/`);
  return (
    <Link
      href={href}
      className={cn(
        "flex items-center gap-2.5 rounded-md px-2 py-1.5 text-sm transition-colors",
        "hover:bg-accent",
        active && "bg-accent text-accent-foreground font-medium",
      )}
    >
      {icon}
      {children}
    </Link>
  );
}
