const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`

export default function DocumentList({ documents, selectedIds, busy, onToggle, onDelete, onSummarize }) {
  if (documents.length === 0) {
    return <p className="text-sm text-stone-500">No papers yet. Upload a PDF to begin.</p>
  }

  return (
    <ul className="space-y-2">
      {documents.map((doc) => {
        const checked = selectedIds.includes(doc.doc_id)
        return (
          <li
            key={doc.doc_id}
            className={`rounded-lg border bg-white p-2.5 text-sm ${checked ? 'border-teal-600' : 'border-stone-200'}`}
          >
            <label className="flex cursor-pointer items-start gap-2">
              <input
                type="checkbox"
                checked={checked}
                onChange={() => onToggle(doc.doc_id)}
                className="mt-1 accent-teal-700"
              />
              <span className="min-w-0">
                <span className="block break-words font-medium">{doc.doc_name}</span>
                <span className="block text-xs text-stone-500">
                  {plural(doc.total_pages, 'page')} · {plural(doc.chunks, 'passage')}
                </span>
              </span>
            </label>
            <div className="mt-2 flex gap-2 pl-6">
              <button
                type="button"
                disabled={busy}
                onClick={() => onSummarize(doc)}
                className="rounded border border-stone-300 px-2 py-0.5 text-xs hover:border-teal-600 hover:text-teal-800 disabled:opacity-50"
              >
                Summarize
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={() => onDelete(doc)}
                className="rounded border border-stone-300 px-2 py-0.5 text-xs text-red-700 hover:border-red-500 disabled:opacity-50"
              >
                Delete
              </button>
            </div>
          </li>
        )
      })}
    </ul>
  )
}