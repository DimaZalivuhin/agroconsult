"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { MessageSquare, Sprout } from "lucide-react";

import { ChatInput } from "@/components/chat-input";
import { useToast } from "@/components/ui/toast";
import { ApiError, chat } from "@/lib/api";

const STARTERS = [
  "Как стать получателем гранта «Агростартап»?",
  "Какие условия льготного кредитования для КФХ?",
  "Можно ли совмещать ЕСХН с другими налоговыми режимами?",
  "Какие документы нужны для подачи на «Семейную ферму»?",
];

function NewChatInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();

  const [value, setValue] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Pre-fill from ?q=... param (from dashboard suggestions)
  useEffect(() => {
    const q = searchParams.get("q");
    if (q) setValue(q);
  }, [searchParams]);

  async function handleSubmit() {
    const question = value.trim();
    if (!question || submitting) return;
    setSubmitting(true);
    try {
      const resp = await chat.ask(question);
      router.push(`/chat/${resp.session_id}`);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Сервис временно недоступен";
      toast({
        title: "Не удалось получить ответ",
        description: message,
        variant: "destructive",
      });
      setSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)] md:h-screen">
      <div className="flex-1 flex items-center justify-center overflow-y-auto">
        <div className="max-w-2xl w-full px-6 py-12 text-center">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-accent mb-4">
            <Sprout className="h-6 w-6 text-primary" />
          </div>
          <h1 className="text-2xl font-medium tracking-tight mb-2">
            Чем можем помочь?
          </h1>
          <p className="text-muted-foreground mb-8">
            Спросите о грантах, субсидиях, налоговых режимах или мерах поддержки АПК. Ответ
            будет основан на актуальных нормативных актах.
          </p>

          <div className="grid sm:grid-cols-2 gap-2 text-left">
            {STARTERS.map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => setValue(q)}
                className="rounded-lg border px-4 py-3 text-sm hover:border-primary/40 hover:bg-accent/30 transition-colors text-left"
              >
                <MessageSquare className="h-4 w-4 text-muted-foreground inline mr-2" />
                {q}
              </button>
            ))}
          </div>
        </div>
      </div>

      <ChatInput
        value={value}
        onChange={setValue}
        onSubmit={handleSubmit}
        loading={submitting}
        disabled={submitting}
      />
    </div>
  );
}

export default function ChatHomePage() {
  return (
    <Suspense fallback={null}>
      <NewChatInner />
    </Suspense>
  );
}
