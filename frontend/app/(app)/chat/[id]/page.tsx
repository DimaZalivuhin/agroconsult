"use client";

import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { Loader2 } from "lucide-react";

import { ChatInput } from "@/components/chat-input";
import { MessageBubble } from "@/components/message-bubble";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { ApiError, chat } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";

export default function SessionPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { toast } = useToast();

  const [messages, setMessages] = useState<ChatMessage[] | null>(null);
  const [value, setValue] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [title, setTitle] = useState<string>("");

  const scrollRef = useRef<HTMLDivElement>(null);

  const loadSession = useCallback(async () => {
    try {
      const s = await chat.session(id);
      setMessages(s.messages);
      setTitle(s.title);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Не удалось загрузить сессию";
      toast({ title: "Ошибка", description: message, variant: "destructive" });
      router.replace("/chat");
    }
  }, [id, router, toast]);

  useEffect(() => {
    if (id) loadSession();
  }, [id, loadSession]);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, submitting]);

  async function handleSubmit() {
    const question = value.trim();
    if (!question || submitting) return;
    setSubmitting(true);

    // Optimistic: show user message immediately
    const tempUserMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      session_id: id,
      role: "user",
      content: question,
      sources: [],
      token_usage: {},
      retrieval_meta: {},
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...(prev ?? []), tempUserMsg]);
    setValue("");

    try {
      const resp = await chat.ask(question, id);
      // Refresh full conversation to get persisted IDs
      await loadSession();
      // Confirm message ID for feedback works
      void resp;
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Сервис временно недоступен";
      toast({
        title: "Не удалось получить ответ",
        description: message,
        variant: "destructive",
      });
      // Remove optimistic message
      setMessages((prev) => prev?.filter((m) => m.id !== tempUserMsg.id) ?? null);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col h-screen">
      <div className="h-14 border-b shrink-0 flex items-center px-6">
        <h2 className="text-sm font-medium truncate">{title || "Загрузка…"}</h2>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        {messages === null && (
          <div className="max-w-3xl mx-auto px-4 py-8 space-y-4">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-32 w-full" />
          </div>
        )}
        {messages && messages.length === 0 && (
          <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
            Сессия пуста
          </div>
        )}
        {messages?.map((m) => (
          <MessageBubble key={m.id} message={m} />
        ))}
        {submitting && (
          <div className="py-6 px-4 md:px-8 bg-muted/30">
            <div className="max-w-3xl mx-auto flex gap-4">
              <div className="h-8 w-8 shrink-0 rounded-md bg-primary text-primary-foreground flex items-center justify-center text-xs font-medium">
                AI
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Ищу ответ в нормативных документах…
              </div>
            </div>
          </div>
        )}
      </div>

      <ChatInput
        value={value}
        onChange={setValue}
        onSubmit={handleSubmit}
        loading={submitting}
        disabled={submitting}
        placeholder="Уточните вопрос или задайте следующий…"
      />
    </div>
  );
}
