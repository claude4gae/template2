export function HeroValuePillarCard({ icon: Icon, label }) {
  return (
    <div className="flex flex-col items-center gap-1">
      <Icon className="size-6 text-primary" />
      <span className="text-sm">{label}</span>
    </div>
  )
}
