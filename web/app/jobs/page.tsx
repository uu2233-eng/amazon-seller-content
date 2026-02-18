"use client";

import { useEffect, useState } from "react";
import StatusBadge from "@/components/status-badge";
import type { ScrapeJob, Audience } from "@/lib/api";

const OUTPUT_FORMATS = [
  { id: "article", label: "图文文案" },
  { id: "short_video", label: "短视频脚本" },
  { id: "long_video", label: "长视频脚本" },
  { id: "image_prompt", label: "图片 Prompt" },
  { id: "social_post", label: "社交帖子" },
];

export default function JobsPage() {
  const [jobs, setJobs] = useState<ScrapeJob[]>([]);
  const [audiences, setAudiences] = useState<Audience[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  // Form state
  const [selectedAudience, setSelectedAudience] = useState("");
  const [selectedFormats, setSelectedFormats] = useState<string[]>(
    OUTPUT_FORMATS.map((f) => f.id)
  );
  const [maxTopics, setMaxTopics] = useState(10);

  const loadData = () => {
    Promise.all([
      fetch("/api/jobs/").then((r) => r.json()),
      fetch("/api/audiences/").then((r) => r.json()),
    ])
      .then(([j, a]) => {
        setJobs(j);
        setAudiences(a);
        if (a.length > 0 && !selectedAudience) setSelectedAudience(a[0].id);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleCreate = async () => {
    if (!selectedAudience) return;
    setCreating(true);
    try {
      await fetch("/api/jobs/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          audience_id: selectedAudience,
          output_formats: selectedFormats,
          max_topics: maxTopics,
        }),
      });
      loadData();
    } finally {
      setCreating(false);
    }
  };

  const toggleFormat = (id: string) => {
    setSelectedFormats((prev) =>
      prev.includes(id) ? prev.filter((f) => f !== id) : [...prev, id]
    );
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">抓取任务</h1>
        <p className="mt-1 text-sm text-gray-500">
          创建和管理内容抓取 → 聚类 → 生成任务
        </p>
      </div>

      {/* Create Job Form */}
      <div className="card mb-8">
        <h2 className="text-lg font-semibold mb-4">创建新任务</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              目标受众
            </label>
            <select
              value={selectedAudience}
              onChange={(e) => setSelectedAudience(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:ring-brand-500"
            >
              {audiences.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              最大话题数
            </label>
            <input
              type="number"
              value={maxTopics}
              onChange={(e) => setMaxTopics(Number(e.target.value))}
              min={1}
              max={50}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:ring-brand-500"
            />
          </div>
          <div className="sm:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              输出格式
            </label>
            <div className="flex flex-wrap gap-2">
              {OUTPUT_FORMATS.map((f) => (
                <button
                  key={f.id}
                  onClick={() => toggleFormat(f.id)}
                  className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                    selectedFormats.includes(f.id)
                      ? "bg-brand-600 text-white"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>
        </div>
        <div className="mt-4">
          <button
            onClick={handleCreate}
            disabled={creating || !selectedAudience}
            className="btn-primary"
          >
            {creating ? "创建中..." : "🚀 启动任务"}
          </button>
        </div>
      </div>

      {/* Jobs List */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">任务历史</h2>
        {loading ? (
          <div className="py-8 text-center text-gray-400">加载中...</div>
        ) : jobs.length === 0 ? (
          <div className="py-8 text-center text-gray-400">暂无任务</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 text-left text-gray-500">
                  <th className="pb-3 font-medium">ID</th>
                  <th className="pb-3 font-medium">受众</th>
                  <th className="pb-3 font-medium">状态</th>
                  <th className="pb-3 font-medium text-right">原始内容</th>
                  <th className="pb-3 font-medium text-right">过滤后</th>
                  <th className="pb-3 font-medium text-right">去重后</th>
                  <th className="pb-3 font-medium text-right">话题</th>
                  <th className="pb-3 font-medium text-right">创意</th>
                  <th className="pb-3 font-medium">时间</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {jobs.map((job) => (
                  <tr key={job.id} className="hover:bg-gray-50">
                    <td className="py-3 font-mono text-xs">#{job.id}</td>
                    <td className="py-3 font-medium">{job.audience_id}</td>
                    <td className="py-3">
                      <StatusBadge status={job.status} />
                    </td>
                    <td className="py-3 text-right">{job.total_raw}</td>
                    <td className="py-3 text-right">{job.total_filtered}</td>
                    <td className="py-3 text-right">{job.total_deduped}</td>
                    <td className="py-3 text-right">{job.total_clusters}</td>
                    <td className="py-3 text-right font-semibold text-brand-600">
                      {job.total_ideas}
                    </td>
                    <td className="py-3 text-xs text-gray-400">
                      {new Date(job.created_at).toLocaleString("zh-CN")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
