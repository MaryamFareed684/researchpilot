import { useEffect, useRef } from 'react'

export default function EvidencePanel({ result, activeN }) {
  const activeRef = useRef(null)

  useEffect(() => {
    activeRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'nearest' })
  }, [activeN, result])

  if (!result) {
    return (
      <p className="text-sm text-stone-500">
        The passages used for an answer appear here, with the paper name and page number.
      </p>
    )
  }

  return (
    <div className="space-y-3">
      {result.citations.length === 0 ? (
        <p className="text-sm text-stone-600">No passage was cited in this answer.</p>
      ) : (
        result.citations.map((c) => {
          const active = c.n === activeN
          return (
            <article
              key={c.n}
              ref={active ? activeRef : null}
              className={`rounded-lg border bg-white p-3 text-sm shadow-sm ${
                active ? 'border-teal-600 ring-2 ring-teal-200' : 'border-stone-200'
              }`}
            >
              <header className="mb-1 flex items-baseline justify-between gap-2">
                <span className="font-semibold text-teal-800">[{c.n}]</span>
                <span className="truncate text-xs text-stone-600">
                  {c.doc_name} · page {c.page}
                </span>
              </header>
              <p className="whitespace-pre-line leading-relaxed text-stone-800">{c.text}</p>
            </article>
          )
        })
      )}

      {result.sources.length > 0 && (
        <details className="text-xs text-stone-600">
          <summary className="cursor-pointer select-none font-medium">
            All {result.sources.length} retrieved passages
          </summary>
          <ul className="mt-2 space-y-1">
            {result.sources.map((s) => (
              <li key={s.n}>
                [{s.n}] {s.doc_name}, page {s.page} · match score {s.score}
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  )
}