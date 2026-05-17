"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  ArrowRight,
  FileText,
  MessageSquarePlus,
  MessageCircle,
  ShieldCheck,
  Sparkles,
  UserCircle,
} from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { chat, documents } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import {
  DIRECTION_LABELS,
  FARM_TYPE_LABELS,
  STATUS_LABELS,
} from "@/lib/types";
import { findRegionByCode } from "@/lib/regions";

const SUGGESTIONS = [
  "Что такое грант «Агростартап» и какие требования для получения?",
  "Чем отличается грант «Семейная ферма» от «Агростартапа»?",
  "Какая ставка по льготному кредитованию для КФХ?",
  "Как получить сельскую ипотеку под 3%?",
  "Какие документы нужны для подачи на компенсирующую субсидию?",
];

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<{ sessions: number; documents: number } | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [s, d] = await Promise.all([
          chat.sessions(),
          documents.list({ limit: 1, is_active: true }),
        ]);
        setStats({ sessions: s.total, documents: d.total });
      } catch {
        setStats({ sessions: 0, documents: 0 });
      }
    }
    load();
  }, []);

  const profile = user?.profile;
  const profileComplete = !!(profile?.region_code && profile?.farm_type);
  const region = findRegionByCode(profile?.region_code);
  const isAdmin = user?.role === "admin";

  return (
    <div className="px-6 py-8 lg:px-10 max-w-6xl mx-auto">
      {/* Greeting */}
      <div className="mb-8">
        <h1 className="text-3xl font-medium tracking-tight">
          Здравствуйте, {user?.full_name || user?.email.split("@")[0]}
        </h1>
        <p className="text-muted-foreground mt-1">
          {profileComplete
            ? `Чем можем помочь сегодня?`
            : "Заполните профиль, чтобы получать более точные ответы по вашему хозяйству"}
        </p>
      </div>

      {/* Action cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        <ActionCard
          href="/chat"
          icon={<MessageSquarePlus className="h-6 w-6 text-primary" />}
          title="Задать вопрос"
          description="Получите консультацию по мерам господдержки со ссылками на нормативные акты"
          highlight
        />
        <ActionCard
          href="/profile"
          icon={<UserCircle className="h-6 w-6 text-primary" />}
          title="Мой профиль"
          description={
            profileComplete
              ? `${region?.name ?? "Регион не указан"} · ${
                  profile?.farm_type ? FARM_TYPE_LABELS[profile.farm_type] : ""
                }`
              : "Заполните для персонализированных ответов"
          }
        />
        <ActionCard
          href="/documents"
          icon={<FileText className="h-6 w-6 text-primary" />}
          title="База документов"
          description={
            stats ? `${stats.documents} нормативных актов в базе` : "Загрузка…"
          }
        />
        <ActionCard
          href="/chat"
          icon={<MessageCircle className="h-6 w-6 text-primary" />}
          title="Мои консультации"
          description={
            stats
              ? stats.sessions === 0
                ? "Пока нет завершённых консультаций"
                : `${stats.sessions} ${pluralize(stats.sessions, "консультация", "консультации", "консультаций")}`
              : "Загрузка…"
          }
        />
        {isAdmin && (
          <ActionCard
            href="/admin"
            icon={<ShieldCheck className="h-6 w-6 text-primary" />}
            title="Админ-панель"
            description="Управление базой документов, статусы индексации"
          />
        )}
      </div>

      {/* Suggested questions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Sparkles className="h-5 w-5 text-primary" />
            Популярные вопросы
          </CardTitle>
          <CardDescription>
            Кликните по вопросу, чтобы открыть консультацию
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          {SUGGESTIONS.map((q) => (
            <Link
              key={q}
              href={`/chat?q=${encodeURIComponent(q)}`}
              className="block rounded-md border px-4 py-3 text-sm hover:border-primary/40 hover:bg-accent/50 transition-colors"
            >
              {q}
            </Link>
          ))}
        </CardContent>
      </Card>

      {/* Profile summary for context */}
      {profileComplete && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="text-base">Учитывается при поиске ответов</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground space-y-1.5">
            <div>
              <span className="text-foreground/70">Регион:</span> {region?.name ?? "не указан"}
            </div>
            <div>
              <span className="text-foreground/70">Форма хозяйствования:</span>{" "}
              {profile?.farm_type ? FARM_TYPE_LABELS[profile.farm_type] : "не указана"}
            </div>
            {profile?.direction && (
              <div>
                <span className="text-foreground/70">Направление:</span>{" "}
                {DIRECTION_LABELS[profile.direction]}
              </div>
            )}
            {profile?.status && (
              <div>
                <span className="text-foreground/70">Статус:</span>{" "}
                {STATUS_LABELS[profile.status]}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function ActionCard({
  href,
  icon,
  title,
  description,
  highlight,
}: {
  href: string;
  icon: React.ReactNode;
  title: string;
  description: string;
  highlight?: boolean;
}) {
  return (
    <Link href={href}>
      <Card
        className={`group cursor-pointer transition-all hover:shadow-sm hover:border-primary/40 ${
          highlight ? "border-primary/30 bg-accent/30" : ""
        }`}
      >
        <CardContent className="p-5 flex items-start gap-4">
          <div className="rounded-md bg-background border p-2.5 shrink-0">{icon}</div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2">
              <h3 className="font-medium">{title}</h3>
              <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{description}</p>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

function pluralize(n: number, one: string, few: string, many: string): string {
  const n10 = n % 10;
  const n100 = n % 100;
  if (n10 === 1 && n100 !== 11) return one;
  if (n10 >= 2 && n10 <= 4 && (n100 < 12 || n100 > 14)) return few;
  return many;
}
