"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { Save } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/components/ui/toast";
import { ApiError, profile as profileApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { REGIONS } from "@/lib/regions";
import {
  DIRECTION_LABELS,
  FARM_TYPE_LABELS,
  STATUS_LABELS,
  type FarmDirection,
  type FarmType,
  type FarmerProfile,
  type FarmerStatus,
} from "@/lib/types";

function ProfileInner() {
  const { user, refresh } = useAuth();
  const searchParams = useSearchParams();
  const isWelcome = searchParams.get("welcome") === "1";
  const { toast } = useToast();

  const [profile, setProfile] = useState<FarmerProfile | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    profileApi
      .get()
      .then(setProfile)
      .catch(() => toast({ title: "Не удалось загрузить профиль", variant: "destructive" }));
  }, [toast]);

  function update<K extends keyof FarmerProfile>(field: K, value: FarmerProfile[K]) {
    setProfile((prev) => (prev ? { ...prev, [field]: value } : prev));
  }

  async function handleSave() {
    if (!profile) return;
    setSaving(true);
    try {
      const region = REGIONS.find((r) => r.code === profile.region_code);
      const payload: Partial<FarmerProfile> = {
        region_code: profile.region_code,
        region_name: region?.name ?? null,
        farm_type: profile.farm_type,
        direction: profile.direction,
        status: profile.status,
        okved: profile.okved,
        years_in_business: profile.years_in_business,
        inn: profile.inn,
      };
      const updated = await profileApi.update(payload);
      setProfile(updated);
      await refresh();
      toast({ title: "Профиль сохранён" });
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Не удалось сохранить";
      toast({ title: "Ошибка", description: message, variant: "destructive" });
    } finally {
      setSaving(false);
    }
  }

  if (!profile) {
    return (
      <div className="px-6 py-8 lg:px-10 max-w-3xl mx-auto">
        <div className="text-muted-foreground text-sm">Загрузка профиля…</div>
      </div>
    );
  }

  return (
    <div className="px-6 py-8 lg:px-10 max-w-3xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-medium tracking-tight">Профиль</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Эти данные используются для подбора мер господдержки, актуальных для вашего хозяйства
        </p>
      </div>

      {isWelcome && (
        <Card className="mb-6 bg-accent/40 border-primary/30">
          <CardContent className="p-4 text-sm">
            <strong>Добро пожаловать!</strong> Заполните профиль — это поможет ассистенту
            подбирать меры господдержки, подходящие именно вашему хозяйству.
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Учётные данные</CardTitle>
          <CardDescription>Эти поля недоступны для редактирования</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex justify-between gap-2">
            <span className="text-muted-foreground">Email</span>
            <span className="font-medium">{user?.email}</span>
          </div>
          {user?.full_name && (
            <div className="flex justify-between gap-2">
              <span className="text-muted-foreground">Имя</span>
              <span className="font-medium">{user.full_name}</span>
            </div>
          )}
          <div className="flex justify-between gap-2">
            <span className="text-muted-foreground">Роль</span>
            <span className="font-medium">
              {user?.role === "admin" ? "Администратор" : "Фермер"}
            </span>
          </div>
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-lg">Характеристики хозяйства</CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="region">Регион</Label>
            <Select
              value={profile.region_code ?? ""}
              onValueChange={(v) => update("region_code", v || null)}
            >
              <SelectTrigger id="region">
                <SelectValue placeholder="Выберите субъект РФ" />
              </SelectTrigger>
              <SelectContent>
                {REGIONS.map((r) => (
                  <SelectItem key={r.code} value={r.code}>
                    {r.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="farm_type">Форма хозяйствования</Label>
            <Select
              value={profile.farm_type ?? ""}
              onValueChange={(v) => update("farm_type", (v || null) as FarmType | null)}
            >
              <SelectTrigger id="farm_type">
                <SelectValue placeholder="Например, КФХ" />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(FARM_TYPE_LABELS).map(([k, label]) => (
                  <SelectItem key={k} value={k}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="direction">Основное направление</Label>
            <Select
              value={profile.direction ?? ""}
              onValueChange={(v) => update("direction", (v || null) as FarmDirection | null)}
            >
              <SelectTrigger id="direction">
                <SelectValue placeholder="Например, молочное скотоводство" />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(DIRECTION_LABELS).map(([k, label]) => (
                  <SelectItem key={k} value={k}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="status">Статус</Label>
            <Select
              value={profile.status ?? ""}
              onValueChange={(v) => update("status", (v || null) as FarmerStatus | null)}
            >
              <SelectTrigger id="status">
                <SelectValue placeholder="Начинающий, действующий…" />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(STATUS_LABELS).map(([k, label]) => (
                  <SelectItem key={k} value={k}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="years">Стаж (лет)</Label>
              <Input
                id="years"
                type="number"
                min={0}
                max={100}
                value={profile.years_in_business ?? ""}
                onChange={(e) =>
                  update(
                    "years_in_business",
                    e.target.value ? Number(e.target.value) : null,
                  )
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="okved">Код ОКВЭД</Label>
              <Input
                id="okved"
                placeholder="Например, 01.42.1"
                value={profile.okved ?? ""}
                onChange={(e) => update("okved", e.target.value || null)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="inn">ИНН (необязательно)</Label>
            <Input
              id="inn"
              maxLength={12}
              value={profile.inn ?? ""}
              onChange={(e) => update("inn", e.target.value || null)}
            />
          </div>

          <div className="pt-2">
            <Button onClick={handleSave} disabled={saving} className="gap-2">
              <Save className="h-4 w-4" />
              {saving ? "Сохранение…" : "Сохранить"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function ProfilePage() {
  return (
    <Suspense fallback={null}>
      <ProfileInner />
    </Suspense>
  );
}
