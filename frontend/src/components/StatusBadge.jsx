const STATUS = {
  answered: {
    label: 'Answered',
    hint: 'Every sentence cites a source. Check the passage to confirm it supports the claim.',
    classes: 'bg-emerald-100 text-emerald-900 ring-emerald-300',
  },
  partially_cited: {
    label: 'Partly cited',
    hint: 'Some sentences have no citation. Check them.',
    classes: 'bg-amber-100 text-amber-900 ring-amber-300',
  },
  unverified: {
    label: 'Unverified',
    hint: 'No valid citation. Do not rely on this answer.',
    classes: 'bg-red-100 text-red-900 ring-red-300',
  },
  no_evidence: {
    label: 'No evidence',
    hint: 'The selected papers do not contain the answer.',
    classes: 'bg-stone-200 text-stone-800 ring-stone-300',
  },
}

export default function StatusBadge({ status }) {
  const info = STATUS[status] ?? STATUS.unverified
  return (
    <p className="flex flex-wrap items-center gap-2 text-sm">
      <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset ${info.classes}`}>
        {info.label}
      </span>
      <span className="text-stone-600">{info.hint}</span>
    </p>
  )
}