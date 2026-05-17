"use client";

import { useEffect, useRef } from "react";
import { ArrowUp, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface Props {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
  loading?: boolean;
  placeholder?: string;
}

export function ChatInput({
  value,
  onChange,
  onSubmit,
  disabled = false,
  loading = false,
  placeholder = "Задайте вопрос о мерах поддержки…",
}: Props) {
  const ref = useRef<HTMLTextAreaElement>(null);

  // Auto-resize on content change
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    const next = Math.min(el.scrollHeight, 200);
    el.style.height = `${next}px`;
  }, [value]);

  function handleKey(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!disabled && value.trim()) onSubmit();
    }
  }

  return (
    <div className="border-t bg-background">
      <div className="max-w-3xl mx-auto px-4 py-4">
        <div
          className={cn(
            "relative rounded-xl border bg-background shadow-sm",
            "focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-primary/10 transition-all",
          )}
        >
          <textarea
            ref={ref}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKey}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            className={cn(
              "w-full resize-none rounded-xl bg-transparent px-4 py-3 pr-14",
              "text-sm focus:outline-none placeholder:text-muted-foreground",
              "disabled:opacity-50",
            )}
            style={{ maxHeight: "200px" }}
          />
          <Button
            type="button"
            size="icon"
            onClick={onSubmit}
            disabled={disabled || !value.trim()}
            className="absolute right-2 bottom-2 h-8 w-8 rounded-lg"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <ArrowUp className="h-4 w-4" />
            )}
          </Button>
        </div>
        <div className="text-xs text-muted-foreground text-center mt-2">
          Enter — отправить · Shift+Enter — новая строка. Сервис носит информационный характер.
        </div>
      </div>
    </div>
  );
}
