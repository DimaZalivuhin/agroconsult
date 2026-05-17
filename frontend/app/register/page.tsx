"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Sprout } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/components/ui/toast";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();
  const { toast } = useToast();

  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [password2, setPassword2] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password.length < 8) {
      toast({
        title: "Слишком короткий пароль",
        description: "Минимум 8 символов",
        variant: "destructive",
      });
      return;
    }
    if (password !== password2) {
      toast({
        title: "Пароли не совпадают",
        variant: "destructive",
      });
      return;
    }

    setSubmitting(true);
    try {
      await register({ email, password, full_name: fullName || undefined });
      router.replace("/profile?welcome=1");
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Не удалось зарегистрироваться";
      toast({ title: "Ошибка регистрации", description: message, variant: "destructive" });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-muted/30 py-8">
      <div className="w-full max-w-md space-y-6">
        <Link href="/" className="flex items-center justify-center gap-2 mb-4">
          <Sprout className="h-7 w-7 text-primary" />
          <span className="font-medium text-xl">AgroConsult</span>
        </Link>

        <Card>
          <CardHeader>
            <CardTitle>Регистрация</CardTitle>
            <CardDescription>
              Создайте аккаунт, чтобы задавать вопросы и сохранять историю консультаций
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="full_name">Имя (необязательно)</Label>
                <Input
                  id="full_name"
                  type="text"
                  autoComplete="name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Пароль</Label>
                <Input
                  id="password"
                  type="password"
                  autoComplete="new-password"
                  required
                  minLength={8}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
                <p className="text-xs text-muted-foreground">Минимум 8 символов</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="password2">Подтвердите пароль</Label>
                <Input
                  id="password2"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={password2}
                  onChange={(e) => setPassword2(e.target.value)}
                />
              </div>
              <Button type="submit" className="w-full" disabled={submitting}>
                {submitting ? "Регистрация…" : "Создать аккаунт"}
              </Button>
            </form>
            <p className="text-sm text-muted-foreground text-center mt-4">
              Уже есть аккаунт?{" "}
              <Link href="/login" className="text-primary hover:underline">
                Войти
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
