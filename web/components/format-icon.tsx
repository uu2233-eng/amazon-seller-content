const FORMAT_MAP: Record<string, { icon: string; label: string; color: string }> = {
  article: { icon: "📝", label: "图文", color: "text-blue-600 bg-blue-50" },
  short_video: { icon: "🎬", label: "短视频", color: "text-pink-600 bg-pink-50" },
  long_video: { icon: "🎥", label: "长视频", color: "text-purple-600 bg-purple-50" },
  image_prompt: { icon: "🖼️", label: "图片", color: "text-orange-600 bg-orange-50" },
  social_post: { icon: "📱", label: "社媒", color: "text-green-600 bg-green-50" },
};

export default function FormatIcon({ format }: { format: string }) {
  const config = FORMAT_MAP[format] || { icon: "📄", label: format, color: "text-gray-600 bg-gray-50" };
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${config.color}`}>
      {config.icon} {config.label}
    </span>
  );
}
