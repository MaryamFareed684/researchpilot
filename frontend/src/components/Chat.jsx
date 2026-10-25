import { useEffect, useRef, useState } from 'react'
import AnswerText from './AnswerText.jsx'
import StatusBadge from './StatusBadge.jsx'

function scopeText(selectedCount) {
  if (selectedCount === 0) return 'Asking all papers'
  return `Asking ${selectedCount} selected paper${selectedCount > 1 ? 's' : ''}`
}

function Message({ message, active, activeN, onCite }) {
  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <p className="max-w-[85%] rounded-2xl rounded-br-sm bg-teal-700 px-3.5 py-2 text-sm text-white">
          {message.text}
        </p>
      </div>
    )
  }

  if (message.kind === 'error') {
    return (
      <p role="alert" className="rounded-lg border border-red-300 bg-red-50 px-3.5 py-2 text-sm text-red-800">
        {message.text}
      </p>
    )
  }

  const { result } = message
  return (
    <article
      className={`space-y-3 rounded-2xl rounded-bl-sm border bg-white p-4 text-sm shadow-sm ${
        active ? 'border-teal-600' : 'border-stone-200'
      }`}
    >
      <StatusBadge status={result.status} />
      <AnswerText text={result.answer} onCite={(n) => onCite(message.id, n)} />
      {result.uncited_sentences?.length > 0 && (
        <div className="rounded-lg bg-amber-50 p-3 text-xs text-amber-900">
          <p className="mb-1 font-semibold">These sentences have no citation:</p>
          <ul className="list-disc space-y-0.5 pl-4">
            {result.uncited_sentences.map((sentence, i) => (
              <li key={i}>{sentence}</li>
            ))}
          </ul>
        </div>
      )}
      {result.invalid_citations?.length > 0 && (
        <p className="text-xs text-red-700">
          The model cited sources that do not exist: {result.invalid_citations.join(', ')}.
        </p>
      )}
      {active && activeN == null && result.citations.length > 0 && (
        <p className="text-xs text-stone-500">Click a [number] to see its passage.</p>
      )}
    </article>
  )
}

export default function Chat({ messages, busy, selectedCount, activeMessageId, activeN, onAsk, onCompare, onCite }) {
  const [text, setText] = useState('')
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'end' })
  }, [messages, busy])

  const canCompare = selectedCount >= 2 && selectedCount <= 3
  const trimmed = text.trim()

  function submit(event) {
    event.preventDefault()
    if (!trimmed || busy) return
    onAsk(trimmed)
    setText('')
  }

  function compare() {
    if (!trimmed || busy || !canCompare) return
    onCompare(trimmed)
    setText('')
  }

  return (
    <div className="flex h-full min-h-[28rem] flex-col">
      <div className="flex-1 space-y-4 overflow-y-auto pr-1">
        {messages.length === 0 && (
          <div className="rounded-xl border border-dashed border-stone-300 p-6 text-sm text-stone-600">
            <p className="mb-2 font-medium text-stone-800">Ask your papers a question.</p>
            <p>
              Answers come only from the papers you upload, and every claim should cite a page. If the papers do not
              contain the answer, ResearchPilot says so.
            </p>
          </div>
        )}
        {messages.map((m) => (
          <Message key={m.id} message={m} active={m.id === activeMessageId} activeN={activeN} onCite={onCite} />
        ))}
        {busy && (
          <p role="status" className="text-sm text-stone-500">
            Searching the papers and writing an answer...
          </p>
        )}
        <div ref={endRef} />
      </div>

      <form onSubmit={submit} className="mt-3 space-y-2 border-t border-stone-200 pt-3">
        <p className="text-xs text-stone-500">{scopeText(selectedCount)}</p>
        <div className="flex gap-2">
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            maxLength={500}
            placeholder="Type a question, or a focus to compare..."
            aria-label="Your question"
            className="min-w-0 flex-1 rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm focus:border-teal-600 focus:outline-none focus:ring-2 focus:ring-teal-200"
          />
          <button
            type="submit"
            disabled={!trimmed || busy}
            className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800 disabled:opacity-50"
          >
            Ask
          </button>
          <button
            type="button"
            onClick={compare}
            disabled={!trimmed || busy || !canCompare}
            title="Select 2 or 3 papers, then type what to compare"
            className="rounded-lg border border-teal-700 px-3 py-2 text-sm font-medium text-teal-800 hover:bg-teal-50 disabled:opacity-40"
          >
            Compare
          </button>
        </div>
      </form>
    </div>
  )
}