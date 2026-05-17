"use client";

import { useState } from "react";
import { ThumbsDown, ThumbsUp, Copy, Check, FileText, ExternalLink } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import { feedback as feedbackApi } from "@/lib/api";
import type { ChatMessage, SourceInfo } from "@/lib/types";
import { cn } from "@/lib/utils";

interface Props {
  message: ChatMessage;
}

export function MessageBubble({ message }: Props) {
  const { toast } = useToast();
  const isUser = message.role === "user";
  const isAssistant = message.role === "assistant";

  const [copied, setCopied] = useState(false);
  const [voted, setVoted] = useState<"up" | "down" | null>(null);

  async function copyToClipboard() {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast({ title: "Не удалось скопировать", variant: "destructive" });
    }
  }

  async function submitFeedback(kind: "positive" | "negative") {
    try {
      await feedbackApi.submit(message.id, kind);
      setVoted(kind === "positive" ? "up" : "down");
      toast({ title: "Спасибо за обратную связь!" });
    } catch {
      toast({ title: "Не удалось отправить", variant: "destructive" });
    }
  }

  return (
    <div className={cn("py-6 px-4 md:px-8", isAssistant && "bg-muted/30")}>
      <div className="max-w-3xl mx-auto flex gap-4">
        {/* Avatar */}
        <div
          className={cn(
            "h-8 w-8 shrink-0 rounded-md flex items-center justify-center text-xs font-medium",
            isUser ? "bg-foreground text-background" : "bg-primary text-primary-foreground",
          )}
        >
          {isUser ? "Я" : "AI"}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0 space-y-3">
          <div className="text-xs text-muted-foreground">
            {isUser ? "Вы" : "AgroConsult"}
          </div>

          {isUser ? (
            <div className="text-sm whitespace-pre-wrap">{message.content}</div>
          ) : (
            <div className="answer-prose text-sm">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
            </div>
          )}

          {isAssistant && message.sources && message.sources.length > 0 && (
            <Sources sources={message.sources} />
          )}

          {isAssistant && (
            <div className="flex items-center gap-1 pt-1">
              <Button
                variant="ghost"
                size="icon"
                onClick={copyToClipboard}
                className="h-7 w-7"
                title="Скопировать"
              >
                {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => submitFeedback("positive")}
                className={cn("h-7 w-7", voted === "up" && "text-primary")}
                title="Полезно"
                disabled={voted !== null}
              >
                <ThumbsUp className="h-3.5 w-3.5" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => submitFeedback("negative")}
                className={cn("h-7 w-7", voted === "down" && "text-destructive")}
                title="Неточно"
                disabled={voted !== null}
              >
                <ThumbsDown className="h-3.5 w-3.5" />
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Sources({ sources }: { sources: SourceInfo[] }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="border rounded-md bg-background overflow-hidden">
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between gap-2 px-3 py-2 text-xs hover:bg-accent/50 transition-colors"
      >
        <span className="flex items-center gap-2 text-muted-foreground">
          <FileText className="h-3.5 w-3.5" />
          Использовано источников: {sources.length}
        </span>
        <span className="text-primary">{expanded ? "Скрыть" : "Показать"}</span>
      </button>
      {expanded && (
        <div className="border-t divide-y">
          {sources.map((s, i) => (
            <div key={s.chunk_id} className="px-3 py-3 text-xs space-y-1">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <span className="citation mr-2">{i + 1}</span>
                  <span className="font-medium">
                    {s.short_title || s.title}
                  </span>
                  {s.doc_number && (
                    <span className="text-muted-foreground"> · № {s.doc_number}</span>
                  )}
                </div>
                {s.source_url && (
                  <a
                    href={s.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline shrink-0 flex items-center gap-0.5"
                  >
                    Оригинал <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </div>
              {s.section_path && (
                <div className="text-muted-foreground">{s.section_path}</div>
              )}
              <div className="text-muted-foreground line-clamp-3 pl-7">{s.snippet}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
