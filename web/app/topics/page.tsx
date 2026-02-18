"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { TopicCluster } from "@/lib/api";

export default function TopicsPage() {
  const [topics, setTopics] = useState<TopicCluster[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/topics/")
      .then((r) => r.json())
      .then(setTopics)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">话题热点</h1>
        <p className="mt-1 text-sm text-gray-500">
          通过 HDBSCAN 聚类发现的 Amazon Seller 热门话题方向
        </p>
      </div>

      {loading ? (
        <div className="py-12 text-center text-gray-400">加载中...</div>
      ) : topics.length === 0 ? (
        <div className="py-12 text-center text-gray-400">
          <p className="text-4xl mb-2">🔍</p>
          <p>还没有话题数据，先运行一次抓取任务</p>
          <Link href="/jobs" className="btn-primary mt-4 inline-flex">
            创建任务
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {topics.map((topic, index) => (
            <div key={topic.id} className="card">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <span className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-orange-400 to-red-500 text-sm font-bold text-white">
                    {index + 1}
                  </span>
                  <div>
                    <h3 className="text-base font-semibold text-gray-900">
                      {topic.label || `Topic #${topic.cluster_index}`}
                    </h3>
                    <div className="mt-1 flex items-center gap-3 text-xs text-gray-500">
                      <span>{topic.size} 条内容</span>
                      <span>·</span>
                      <span>互动总分 {topic.total_engagement.toFixed(0)}</span>
                      <span>·</span>
                      <span>来源: {topic.sources.join(", ")}</span>
                    </div>
                  </div>
                </div>
                <Link
                  href={`/ideas?cluster_id=${topic.id}`}
                  className="btn-secondary text-xs"
                >
                  查看创意 →
                </Link>
              </div>

              {/* Top Titles */}
              {topic.top_titles.length > 0 && (
                <div className="mt-4 space-y-1.5">
                  <p className="text-xs font-medium text-gray-500">热门标题:</p>
                  {topic.top_titles.slice(0, 3).map((title, i) => (
                    <div
                      key={i}
                      className="flex items-center gap-2 rounded-lg bg-gray-50 px-3 py-2 text-sm"
                    >
                      <span className="text-gray-400">{i + 1}.</span>
                      <span>{title}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Representative Body Preview */}
              {topic.representative_body && (
                <div className="mt-3">
                  <p className="text-xs text-gray-400 line-clamp-2">
                    {topic.representative_body.slice(0, 200)}...
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
