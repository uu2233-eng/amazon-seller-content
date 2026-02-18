"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import StatCard from "@/components/stat-card";
import StatusBadge from "@/components/status-badge";
import type { DashboardStats } from "@/lib/api";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/dashboard/stats")
      .then((r) => r.json())
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Amazon Seller 内容引擎概览
        </p>
      </div>

      {/* Stats Cards */}
      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="抓取任务"
          value={stats?.total_jobs ?? "—"}
          icon="🔄"
          color="blue"
        />
        <StatCard
          title="采集内容"
          value={stats?.total_contents ?? "—"}
          icon="📦"
          color="green"
        />
        <StatCard
          title="话题簇"
          value={stats?.total_clusters ?? "—"}
          icon="🔥"
          color="orange"
        />
        <StatCard
          title="内容创意"
          value={stats?.total_ideas ?? "—"}
          icon="💡"
          color="purple"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recent Jobs */}
        <div className="card">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold">最近任务</h2>
            <Link href="/jobs" className="text-sm text-brand-600 hover:underline">
              查看全部 →
            </Link>
          </div>
          {!stats?.recent_jobs?.length ? (
            <div className="py-8 text-center text-gray-400">
              <p className="text-4xl mb-2">🚀</p>
              <p>还没有任务，去创建第一个吧</p>
              <Link href="/jobs" className="btn-primary mt-4 inline-flex">
                创建任务
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {stats.recent_jobs.map((job) => (
                <Link
                  key={job.id}
                  href={`/jobs`}
                  className="flex items-center justify-between rounded-lg border border-gray-100 p-3 transition-colors hover:bg-gray-50"
                >
                  <div>
                    <span className="text-sm font-medium">{job.audience_id}</span>
                    <span className="ml-2 text-xs text-gray-400">
                      #{job.id}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-500">
                      {job.total_ideas} 创意
                    </span>
                    <StatusBadge status={job.status} />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Top Topics */}
        <div className="card">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold">热门话题</h2>
            <Link href="/topics" className="text-sm text-brand-600 hover:underline">
              查看全部 →
            </Link>
          </div>
          {!stats?.top_topics?.length ? (
            <div className="py-8 text-center text-gray-400">
              <p className="text-4xl mb-2">🔥</p>
              <p>运行一次抓取任务后，热门话题会出现在这里</p>
            </div>
          ) : (
            <div className="space-y-3">
              {stats.top_topics.slice(0, 5).map((topic) => (
                <div
                  key={topic.id}
                  className="rounded-lg border border-gray-100 p-3"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">
                      {topic.label || `Topic #${topic.cluster_index}`}
                    </span>
                    <span className="text-xs text-gray-400">
                      {topic.size} 条内容
                    </span>
                  </div>
                  <div className="mt-1 flex gap-1">
                    {topic.sources.map((s) => (
                      <span key={s} className="badge-gray text-[10px]">{s}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick Start Guide */}
      <div className="mt-8 card bg-gradient-to-r from-brand-50 to-blue-50 border-brand-200">
        <h2 className="text-lg font-semibold mb-3">快速开始</h2>
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="flex gap-3">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-600 text-sm font-bold text-white">
              1
            </span>
            <div>
              <p className="text-sm font-medium">配置 API Key</p>
              <p className="text-xs text-gray-500">在 .env 中设置 OpenAI 和数据源的密钥</p>
            </div>
          </div>
          <div className="flex gap-3">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-600 text-sm font-bold text-white">
              2
            </span>
            <div>
              <p className="text-sm font-medium">选择受众</p>
              <p className="text-xs text-gray-500">在「受众管理」中选择目标人群</p>
            </div>
          </div>
          <div className="flex gap-3">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-600 text-sm font-bold text-white">
              3
            </span>
            <div>
              <p className="text-sm font-medium">启动抓取</p>
              <p className="text-xs text-gray-500">创建任务，系统自动完成抓取→聚类→生成</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
