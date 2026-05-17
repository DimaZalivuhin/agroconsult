"use client";

import { useEffect, useState } from "react";
import { ExternalLink, FileText, Filter } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { documents } from "@/lib/api";
import {
  DOCUMENT_TYPE_LABELS,
  type DocumentType,
  type LegalDocument,
} from "@/lib/types";

export default function DocumentsPage() {
  const [items, setItems] = useState<LegalDocument[] | null>(null);
  const [total, setTotal] = useState(0);
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("all");

  useEffect(() => {
    setItems(null);
    documents
      .list({ limit: 200, is_active: true })
      .then((r) => {
        setItems(r.items);
        setTotal(r.total);
      })
      .catch(() => {
        setItems([]);
        setTotal(0);
      });
  }, []);

  const filtered = (items ?? []).filter((doc) => {
    if (typeFilter !== "all" && doc.doc_type !== typeFilter) return false;
    if (query) {
      const q = query.toLowerCase();
      return (
        doc.title.toLowerCase().includes(q) ||
        doc.short_title?.toLowerCase().includes(q) ||
        doc.doc_number?.toLowerCase().includes(q) ||
        doc.issuing_body?.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="px-6 py-8 lg:px-10 max-w-6xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-medium tracking-tight">База документов</h1>
        <p className="text-muted-foreground text-sm mt-1">
          {total} нормативно-правовых актов в базе знаний сервиса
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-3 mb-6">
        <div className="flex-1 min-w-[240px]">
          <Input
            placeholder="Поиск по названию, номеру или органу…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <div className="w-72">
          <Select value={typeFilter} onValueChange={setTypeFilter}>
            <SelectTrigger>
              <Filter className="h-4 w-4 mr-2 text-muted-foreground" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Все типы</SelectItem>
              {Object.entries(DOCUMENT_TYPE_LABELS).map(([k, label]) => (
                <SelectItem key={k} value={k}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {items === null && (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      )}

      {items && filtered.length === 0 && (
        <Card>
          <CardContent className="p-10 text-center text-muted-foreground">
            Ничего не найдено
          </CardContent>
        </Card>
      )}

      <div className="space-y-3">
        {filtered.map((doc) => (
          <DocCard key={doc.id} doc={doc} />
        ))}
      </div>
    </div>
  );
}

function DocCard({ doc }: { doc: LegalDocument }) {
  return (
    <Card className="hover:border-primary/30 transition-colors">
      <CardContent className="p-5">
        <div className="flex items-start gap-4">
          <div className="rounded-md bg-accent p-2 shrink-0">
            <FileText className="h-5 w-5 text-primary" />
          </div>
          <div className="flex-1 min-w-0 space-y-2">
            <div>
              <div className="text-xs text-muted-foreground mb-1 flex flex-wrap gap-x-3 gap-y-1">
                <span className="bg-secondary px-2 py-0.5 rounded">
                  {DOCUMENT_TYPE_LABELS[doc.doc_type as DocumentType] ?? doc.doc_type}
                </span>
                {doc.doc_number && <span>№ {doc.doc_number}</span>}
                {doc.doc_date && <span>от {formatDate(doc.doc_date)}</span>}
                {doc.issuing_body && <span>{doc.issuing_body}</span>}
              </div>
              <h3 className="font-medium leading-snug">
                {doc.short_title || doc.title}
              </h3>
              {doc.short_title && doc.short_title !== doc.title && (
                <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                  {doc.title}
                </p>
              )}
            </div>
            {doc.summary && (
              <p className="text-sm text-muted-foreground leading-relaxed">
                {doc.summary}
              </p>
            )}
            <div className="flex items-center gap-4 text-xs text-muted-foreground pt-1">
              <span>{doc.chunk_count} фрагментов в индексе</span>
              {doc.source_url && (
                <a
                  href={doc.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline flex items-center gap-1"
                >
                  Оригинал <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}
