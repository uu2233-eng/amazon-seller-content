"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import FormatIcon from "@/components/format-icon";
import type { ContentIdea } from "@/lib/api";

function IdeasContent() {
  const searchParams = useSearchParams();
  const clusterId = searchParams.get("cluster_id");

  const [ideas, setIdeas] = useState<ContentIdea[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedIdea, setSelectedIdea] = useState<ContentIdea | null>(null);
  const [filterFormat, setFilterFormat] = useState<string>("");

  useEffect(() => {
    const params = new URLSearchParams();
    if (clusterId) params.set("cluster_id", clusterId);
    if (filterFormat) params.set("format_type", filterFormat);

    fetch(`/api/ideas/?${params.toString()}`)
      .then((r) => r.json())
      .then((data) => {
        setIdeas(data);
        if (data.length > 0 && !selectedIdea) setSelectedIdea(data[0]);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [clusterId, filterFormat]);

  const toggleFavorite = async (idea: ContentIdea) => {
    try {
      const res = await fetch(`/api/ideas/${idea.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_favorite: !idea.is_favorite }),
      });
      const updated = await res.json();
      setIdeas((prev) => prev.map((i) => (i.id === updated.id ? updated : i)));
      if (selectedIdea?.id === updated.id) setSelectedIdea(updated);
    } catch {}
  };

  const formats = ["", "article", "short_video", "long_video", "image_prompt", "social_post"];
  const formatLabels: Record<string, string> = {
    "": "全部",
    article: "📝 图文",
    short_video: "🎬 短视频",
    long_video: "🎥 长视频",
    image_prompt: "🖼️ 图片",
    social_post: "📱 社媒",
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">内容创意</h1>
        <p className="mt-1 text-sm text-gray-500">
          AI 生成的内容创意 — 文案、脚本、图片 Prompt
          {clusterId && <span className="ml-2 badge-blue">话题 #{clusterId}</span>}
        </p>
      </div>

      {/* Format Filter */}
      <div className="mb-6 flex flex-wrap gap-2">
        {formats.map((f) => (
          <button
            key={f}
            onClick={() => setFilterFormat(f)}
            className={`rounded-full px-4 py-1.5 text-xs font-medium transition-colors ${
              filterFormat === f
                ? "bg-brand-600 text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            {formatLabels[f]}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="py-12 text-center text-gray-400">加载中...</div>
      ) : ideas.length === 0 ? (
        <div className="py-12 text-center text-gray-400">
          <p className="text-4xl mb-2">💡</p>
          <p>暂无内容创意</p>
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[340px_1fr]">
          {/* Ideas List */}
          <div className="space-y-2 max-h-[calc(100vh-200px)] overflow-y-auto pr-2">
            {ideas.map((idea) => (
              <button
                key={idea.id}
                onClick={() => setSelectedIdea(idea)}
                className={`w-full rounded-lg border p-3 text-left transition-colors ${
                  selectedIdea?.id === idea.id
                    ? "border-brand-500 bg-brand-50"
                    : "border-gray-200 hover:bg-gray-50"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <FormatIcon format={idea.format_type} />
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleFavorite(idea);
                    }}
                    className="text-lg"
                  >
                    {idea.is_favorite ? "⭐" : "☆"}
                  </button>
                </div>
                <p className="text-sm font-medium line-clamp-2">
                  {idea.topic_label}
                </p>
                <p className="mt-1 text-xs text-gray-400">
                  {new Date(idea.created_at).toLocaleDateString("zh-CN")}
                </p>
              </button>
            ))}
          </div>

          {/* Content Preview */}
          <div className="card max-h-[calc(100vh-200px)] overflow-y-auto">
            {selectedIdea ? (
              <div>
                <div className="mb-4 flex items-center justify-between border-b border-gray-200 pb-4">
                  <div>
                    <h2 className="text-lg font-semibold">
                      {selectedIdea.topic_label}
                    </h2>
                    <div className="mt-1 flex items-center gap-2">
                      <FormatIcon format={selectedIdea.format_type} />
                      <span className="text-xs text-gray-400">
                        受众: {selectedIdea.audience_id}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => toggleFavorite(selectedIdea)}
                    className="text-2xl"
                  >
                    {selectedIdea.is_favorite ? "⭐" : "☆"}
                  </button>
                </div>

                {/* Generated Content */}
                <div className="prose max-w-none whitespace-pre-wrap text-sm leading-relaxed">
                  {selectedIdea.generated_content}
                </div>

                {/* Source URLs */}
                {selectedIdea.source_urls.length > 0 && (
                  <div className="mt-6 border-t border-gray-200 pt-4">
                    <p className="text-xs font-medium text-gray-500 mb-2">
                      参考来源:
                    </p>
                    <div className="space-y-1">
                      {selectedIdea.source_urls.map((url, i) => (
                        <a
                          key={i}
                          href={url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block text-xs text-brand-600 hover:underline truncate"
                        >
                          {url}
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="py-12 text-center text-gray-400">
                ← 选择一条创意查看详情
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function IdeasPage() {
  return (
    <Suspense fallback={<div className="py-12 text-center text-gray-400">加载中...</div>}>
      <IdeasContent />
    </Suspense>
  );
}
