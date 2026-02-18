import { clsx } from "clsx";

const STATUS_CONFIG: Record<string, { label: string; className: string }> = {
  pending: { label: "等待中", className: "badge-yellow" },
  running: { label: "运行中", className: "badge-blue" },
  completed: { label: "已完成", className: "badge-green" },
  failed: { label: "失败", className: "badge-red" },
};

export default function StatusBadge({ status }: { status: string }) {
  const config = STATUS_CONFIG[status] || {
    label: status,
    className: "badge-gray",
  };
  return <span className={config.className}>{config.label}</span>;
}
