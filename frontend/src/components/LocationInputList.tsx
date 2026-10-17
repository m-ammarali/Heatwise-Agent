import type { LocationIn } from "../types/api";
import { CloseIcon } from "./icons";

interface Props {
  locations: LocationIn[];
  onChange: (locations: LocationIn[]) => void;
}

const input =
  "w-full rounded-md border border-line-strong bg-white px-3 py-2.5 text-[15px] placeholder:text-ink-3 focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/20";

export default function LocationInputList({ locations, onChange }: Props) {
  function update(index: number, field: keyof LocationIn, value: string) {
    const next = [...locations];
    if (field === "name") {
      next[index] = { ...next[index], name: value };
    } else {
      const num = parseFloat(value);
      next[index] = { ...next[index], [field]: Number.isNaN(num) ? 0 : num };
    }
    onChange(next);
  }

  return (
    <div>
      <div className="hidden sm:grid grid-cols-[2rem_1fr_9rem_9rem_2rem] gap-3 px-1 pb-2 text-xs font-semibold uppercase tracking-wider text-ink-3">
        <span />
        <span>Site name</span>
        <span>Latitude</span>
        <span>Longitude</span>
        <span />
      </div>
      <div className="space-y-3">
        {locations.map((loc, i) => (
          <div key={i} className="grid grid-cols-2 sm:grid-cols-[2rem_1fr_9rem_9rem_2rem] gap-3 items-center">
            <span className="hidden sm:flex w-7 h-7 rounded-full bg-brand-soft text-brand text-xs font-bold items-center justify-center">
              {String.fromCharCode(65 + i)}
            </span>
            <input
              className={`${input} col-span-2 sm:col-span-1`}
              placeholder="e.g. Anarkali Bazaar"
              aria-label={`Site ${i + 1} name`}
              value={loc.name}
              onChange={(e) => update(i, "name", e.target.value)}
            />
            <input
              className={`${input} tnum`}
              placeholder="31.5667"
              inputMode="decimal"
              aria-label={`Site ${i + 1} latitude`}
              value={loc.latitude || ""}
              onChange={(e) => update(i, "latitude", e.target.value)}
            />
            <input
              className={`${input} tnum`}
              placeholder="74.3097"
              inputMode="decimal"
              aria-label={`Site ${i + 1} longitude`}
              value={loc.longitude || ""}
              onChange={(e) => update(i, "longitude", e.target.value)}
            />
            {locations.length > 1 ? (
              <button
                onClick={() => onChange(locations.filter((_, k) => k !== i))}
                className="justify-self-end text-ink-3 hover:text-ink p-1.5 rounded hover:bg-soft"
                aria-label={`Remove ${loc.name || `site ${i + 1}`}`}
              >
                <CloseIcon />
              </button>
            ) : <span />}
          </div>
        ))}
      </div>
      {locations.length < 5 && (
        <button
          onClick={() => onChange([...locations, { name: "", latitude: 0, longitude: 0 }])}
          className="mt-4 text-sm font-medium text-brand hover:text-brand-dark"
        >
          + Add another site <span className="text-ink-3 font-normal">({locations.length} of 5)</span>
        </button>
      )}
    </div>
  );
}
