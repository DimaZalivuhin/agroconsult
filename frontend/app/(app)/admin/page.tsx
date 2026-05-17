"use client";

import { useEffect, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Loader2,
  RefreshCw,
  ShieldCheck,
  Trash2,
  Upload,
} from "lucide-react";

import { RequireAuth } from "@/components/require-auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/toast";
import { ApiError, getToken } from "@/lib/api";
import {
  DOCUMENT_TYPE_LABELS,
  type DocumentType,
  type LegalDocument,
} from "@/lib/types";
import { cn } from "@/lib/utils";

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

function StatusBadge({ status }: { status: LegalDocument["status"] }) {
  const map: Record<LegalDocument["status"], { label: string; cls: string; icon: React.ReactNode }> = {
    pending: { label: "В очереди", cls: "bg-muted text-muted-foreground", icon: <Clock className="h-3 w-3" /> },
    parsing: { label: "Парсинг", cls: "bg-blue-100 text-blue-800", icon: <Loader2 className="h-3 w-3 animate-spin" /> },
    chunking: { label: "Разбиение", cls: "bg-blue-100 text-blue-800", icon: <Loader2 className="h-3 w-3 animate-spin" /> },
    embedding: { label: "Векторизация", cls: "bg-blue-100 text-blue-800", icon: <Loader2 className="h-3 w-3 animate-spin" /> },
    indexed: { label: "Готов", cls: "bg-accent text-accent-foreground", icon: <CheckCircle2 className="h-3 w-3" /> },
    failed: { label: "Ошибка", cls: "bg-destructive/10 text-destructive", icon: <AlertCircle className="h-3 w-3" /> },
    archived: { label: "Архив", cls: "bg-muted text-muted-foreground", icon: null },
  };
  const v = map[status];
  return (
    <span className={cn("inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full", v.cls)}>
      {v.icon}
      {v.label}
    </span>
  );
}

function AdminInner() {
  const { toast } = useToast();
  const [items, setItems] = useState<LegalDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  // Upload form state
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [shortTitle, setShortTitle] = useState("");
  const [docType, setDocType] = useState<DocumentType>("government_decree");
  const [docNumber, setDocNumber] = useState("");
  const [docDate, setDocDate] = useState("");
  const [issuingBody, setIssuingBody] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [summary, setSummary] = useState("");

  async function load() {
    setLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/api/v1/documents?limit=200`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      const data = await resp.json();
      setItems(data.items ?? []);
    } catch {
      toast({ title: "Не удалось загрузить список", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // Auto-refresh while there are in-progress docs
    const t = setInterval(() => {
      setItems((prev) => {
        const hasInProgress = prev.some((d) =>
          ["pending", "parsing", "chunking", "embedding"].includes(d.status),
        );
        if (hasInProgress) load();
        return prev;
      });
    }, 5000);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!file) {
      toast({ title: "Файл не выбран", variant: "destructive" });
      return;
    }
    if (!title.trim()) {
      toast({ title: "Введите название", variant: "destructive" });
      return;
    }
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("title", title);
      form.append("doc_type", docType);
      if (shortTitle) form.append("short_title", shortTitle);
      if (docNumber) form.append("doc_number", docNumber);
      if (docDate) form.append("doc_date", docDate);
      if (issuingBody) form.append("issuing_body", issuingBody);
      if (sourceUrl) form.append("source_url", sourceUrl);
      if (summary) form.append("summary", summary);

      const resp = await fetch(`${API_BASE}/api/v1/documents/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` },
        body: form,
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => null);
        throw new ApiError(err?.detail || "Не удалось загрузить", resp.status, err);
      }

      toast({ title: "Документ загружен, индексация запущена" });
      // Reset form
      setFile(null);
      setTitle("");
      setShortTitle("");
      setDocNumber("");
      setDocDate("");
      setIssuingBody("");
      setSourceUrl("");
      setSummary("");
      const input = document.getElementById("upload-file") as HTMLInputElement | null;
      if (input) input.value = "";
      await load();
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Не удалось загрузить";
      toast({ title: "Ошибка", description: message, variant: "destructive" });
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Удалить документ и все его векторы?")) return;
    try {
      const resp = await fetch(`${API_BASE}/api/v1/documents/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (!resp.ok) throw new Error();
      toast({ title: "Документ удалён" });
      await load();
    } catch {
      toast({ title: "Не удалось удалить", variant: "destructive" });
    }
  }

  return (
    <div className="px-6 py-8 lg:px-10 max-w-6xl mx-auto">
      <div className="mb-6 flex items-center gap-3">
        <div className="rounded-md bg-accent p-2">
          <ShieldCheck className="h-5 w-5 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-medium tracking-tight">Админ-панель</h1>
          <p className="text-muted-foreground text-sm">
            Управление базой нормативных документов
          </p>
        </div>
      </div>

      {/* Upload form */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Upload className="h-4 w-4" />
            Загрузить документ
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleUpload} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="upload-file">Файл (PDF / HTML / TXT)</Label>
                <Input
                  id="upload-file"
                  type="file"
                  accept=".pdf,.html,.htm,.txt,.md"
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="doc_type">Тип документа</Label>
                <Select value={docType} onValueChange={(v) => setDocType(v as DocumentType)}>
                  <SelectTrigger id="doc_type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(DOCUMENT_TYPE_LABELS).map(([k, label]) => (
                      <SelectItem key={k} value={k}>
                        {label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="title">Полное название</Label>
              <Input
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Постановление Правительства РФ от ..."
                required
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="short_title">Короткое название</Label>
                <Input
                  id="short_title"
                  value={shortTitle}
                  onChange={(e) => setShortTitle(e.target.value)}
                  placeholder="ПП РФ № 1528"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="doc_number">Номер</Label>
                <Input
                  id="doc_number"
                  value={docNumber}
                  onChange={(e) => setDocNumber(e.target.value)}
                  placeholder="1528"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="doc_date">Дата</Label>
                <Input
                  id="doc_date"
                  type="date"
                  value={docDate}
                  onChange={(e) => setDocDate(e.target.value)}
                />
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="issuing_body">Орган</Label>
                <Input
                  id="issuing_body"
                  value={issuingBody}
                  onChange={(e) => setIssuingBody(e.target.value)}
                  placeholder="Правительство РФ"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="source_url">Ссылка на источник</Label>
                <Input
                  id="source_url"
                  value={sourceUrl}
                  onChange={(e) => setSourceUrl(e.target.value)}
                  placeholder="http://pravo.gov.ru/..."
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="summary">Краткое описание (по желанию)</Label>
              <Textarea
                id="summary"
                value={summary}
                onChange={(e) => setSummary(e.target.value)}
                rows={3}
              />
            </div>
            <Button type="submit" disabled={uploading} className="gap-2">
              {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
              {uploading ? "Загрузка…" : "Загрузить"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Documents list */}
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-medium">Документы в базе ({items.length})</h2>
        <Button variant="outline" size="sm" onClick={load} disabled={loading} className="gap-1.5">
          <RefreshCw className={cn("h-3.5 w-3.5", loading && "animate-spin")} />
          Обновить
        </Button>
      </div>

      <div className="space-y-2">
        {items.map((doc) => (
          <Card key={doc.id}>
            <CardContent className="p-4 flex items-center justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <StatusBadge status={doc.status} />
                  <span className="text-xs text-muted-foreground">
                    {DOCUMENT_TYPE_LABELS[doc.doc_type as DocumentType]}
                  </span>
                  {doc.doc_number && (
                    <span className="text-xs text-muted-foreground">№ {doc.doc_number}</span>
                  )}
                  <span className="text-xs text-muted-foreground">
                    {doc.chunk_count} фрагментов
                  </span>
                </div>
                <div className="text-sm font-medium truncate">
                  {doc.short_title || doc.title}
                </div>
                {doc.error_message && (
                  <div className="text-xs text-destructive mt-1">{doc.error_message}</div>
                )}
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => handleDelete(doc.id)}
                title="Удалить"
              >
                <Trash2 className="h-4 w-4 text-muted-foreground" />
              </Button>
            </CardContent>
          </Card>
        ))}
        {!loading && items.length === 0 && (
          <Card>
            <CardContent className="p-10 text-center text-muted-foreground">
              В базе пока нет документов
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

export default function AdminPage() {
  return (
    <RequireAuth adminOnly>
      <AdminInner />
    </RequireAuth>
  );
}
