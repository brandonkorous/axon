export function ToggleRow({
  label,
  description,
  checked,
  onChange,
}: {
  label: string;
  description: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <label className="flex items-center justify-between gap-3 cursor-pointer">
      <div>
        <span className="text-sm">{label}</span>
        <p className="text-xs text-base-content/60 mt-0.5">{description}</p>
      </div>
      <input
        type="checkbox"
        className="toggle toggle-sm toggle-primary"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
      />
    </label>
  );
}
