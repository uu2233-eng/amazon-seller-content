"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { Audience } from "@/lib/api";

export default function AudiencesPage() {
  const [audiences, setAudiences] = useState<Audience[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/audiences/")
      .then((r) => r.json())
      .then(setAudiences)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">受众管理</h1>
        <p className="mt-1 text-sm text-gray-500">
          管理 Amazon Seller 目标受众群体与关键词库
        </p>
      </div>

      {loading ? (
        <div className="py-12 text-center text-gray-400">加载中...</div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {audiences.map((audience) => (
            <div key={audience.id} className="card group">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-base font-semibold text-gray-900">
                    {audience.name}
                  </h3>
                  <p className="mt-1 text-xs text-gray-500">
                    {audience.description}
                  </p>
                </div>
                <span
                  className={`badge ${audience.is_active ? "badge-green" : "badge-gray"}`}
                >
                  {audience.is_active ? "启用" : "禁用"}
                </span>
              </div>

              <div className="mt-4 space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">关键词数</span>
                  <span className="font-medium">{audience.keyword_count}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">Subreddits</span>
                  <span className="font-medium">
                    {audience.subreddits?.length || 0}
                  </span>
                </div>
              </div>

              {/* Sample keywords */}
              <div className="mt-4">
                <p className="text-xs font-medium text-gray-500 mb-2">核心关键词:</p>
                <div className="flex flex-wrap gap-1">
                  {audience.core_keywords?.slice(0, 4).map((kw) => (
                    <span key={kw} className="badge-blue text-[10px]">
                      {kw}
                    </span>
                  ))}
                  {(audience.core_keywords?.length || 0) > 4 && (
                    <span className="badge-gray text-[10px]">
                      +{audience.core_keywords.length - 4}
                    </span>
                  )}
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-gray-100">
                <Link
                  href={`/jobs?audience=${audience.id}`}
                  className="text-sm text-brand-600 hover:underline"
                >
                  启动抓取 →
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
