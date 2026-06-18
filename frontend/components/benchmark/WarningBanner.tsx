interface Props {
  message: string
  type?: "warning" | "info"
}

export default function WarningBanner({ message, type = "info" }: Props) {
  const styles =
    type === "warning"
      ? "border-amber-200 bg-amber-50 text-amber-800"
      : "border-blue-200 bg-blue-50 text-blue-800"
  return (
    <div className={`rounded-xl border px-5 py-3 text-sm ${styles}`}>
      {message}
    </div>
  )
}
