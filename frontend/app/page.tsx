"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Sprout, FileText, MessageSquare, ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";

export default function HomePage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) router.replace("/dashboard");
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-muted-foreground text-sm">Загрузка…</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b">
        <div className="container flex items-center justify-between h-16">
          <div className="flex items-center gap-2">
            <Sprout className="h-6 w-6 text-primary" />
            <span className="font-medium text-lg">AgroConsult</span>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/login">
              <Button variant="ghost">Войти</Button>
            </Link>
            <Link href="/register">
              <Button>Регистрация</Button>
            </Link>
          </div>
        </div>
      </header>

      <section className="container py-20 max-w-4xl">
        <h1 className="text-4xl md:text-5xl font-medium tracking-tight mb-4">
          Консультант по мерам государственной поддержки сельхозпроизводителей
        </h1>
        <p className="text-lg text-muted-foreground mb-8 max-w-3xl">
          Задайте вопрос на простом языке — получите ответ со ссылками на нормативные акты:
          грант «Агростартап», «Семейная ферма», льготное кредитование, субсидии,
          сельская ипотека. Каждый ответ опирается на актуальные федеральные законы,
          постановления Правительства и приказы Минсельхоза России.
        </p>
        <div className="flex flex-wrap gap-3">
          <Link href="/register">
            <Button size="lg">Начать бесплатно</Button>
          </Link>
          <Link href="/login">
            <Button size="lg" variant="outline">Войти</Button>
          </Link>
        </div>
      </section>

      <section className="container pb-20 grid md:grid-cols-3 gap-6">
        <FeatureCard
          icon={<MessageSquare className="h-7 w-7 text-primary" />}
          title="Ответы за секунды"
          text="Сервис ищет ответ в базе нормативных актов и формулирует его на понятном языке — никаких длинных канцелярских формулировок."
        />
        <FeatureCard
          icon={<FileText className="h-7 w-7 text-primary" />}
          title="Со ссылками на НПА"
          text="Каждое утверждение в ответе подкрепляется источником: вы видите, на какой именно документ опирается консультация."
        />
        <FeatureCard
          icon={<ShieldCheck className="h-7 w-7 text-primary" />}
          title="Учёт вашего профиля"
          text="Регион, форма хозяйствования и направление деятельности учитываются при подборе мер поддержки, актуальных для вас."
        />
      </section>

      <footer className="border-t py-8 mt-auto">
        <div className="container text-sm text-muted-foreground flex justify-between flex-wrap gap-2">
          <span>AgroConsult — ВКР, РГАУ-МСХА им. К.А. Тимирязева, 2026.</span>
          <span>Сервис носит информационный характер и не заменяет официальные консультации.</span>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({ icon, title, text }: { icon: React.ReactNode; title: string; text: string }) {
  return (
    <div className="rounded-lg border p-6 space-y-3 hover:border-primary/30 transition-colors">
      {icon}
      <h3 className="font-medium text-lg">{title}</h3>
      <p className="text-sm text-muted-foreground leading-relaxed">{text}</p>
    </div>
  );
}
