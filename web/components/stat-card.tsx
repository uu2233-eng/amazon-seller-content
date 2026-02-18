interface StatCardProps {
  title: string;
  value: string | number;
  icon: string;
  change?: string;
  color?: "blue" | "green" | "orange" | "purple";
}

const colorMap = {
  blue: "bg-blue-50 text-blue-600",
  green: "bg-green-50 text-green-600",
  orange: "bg-orange-50 text-orange-600",
  purple: "bg-purple-50 text-purple-600",
};

export default function StatCard({
  title,
  value,
  icon,
  change,
  color = "blue",
}: StatCardProps) {
  return (
    <div className="card flex items-center gap-4">
      <div
        className={`flex h-12 w-12 items-center justify-center rounded-xl text-2xl ${colorMap[color]}`}
      >
        {icon}
      </div>
      <div>
        <p className="text-sm text-gray-500">{title}</p>
        <p className="text-2xl font-bold">{value}</p>
        {change && <p className="text-xs text-green-600">{change}</p>}
      </div>
    </div>
  );
}
