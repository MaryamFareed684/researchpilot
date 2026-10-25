import { useCallback, useEffect, useRef, useState } from 'react'
import { askQuestion, compareDocuments, deleteDocument, listDocuments, summarizeDocument } from './api.js'
import Chat from './components/Chat.jsx'
import DocumentList from './components/DocumentList.jsx'
import EvidencePanel from './components/EvidencePanel.jsx'
import UploadBox from './components/UploadBox.jsx'

export default function App() {
  const [documents, setDocuments] = useState([])
  const [selectedIds, setSelectedIds] = useState([])
  const [messages, setMessages] = useState([])
  const [busy, setBusy] = useState(false)
  const [loadError, setLoadError] = useState('')
  const [activeMessageId, setActiveMessageId] = useState(null)
  const [activeN, setActiveN] = useState(null)
  const nextId = useRef(1)

  const refreshDocuments = useCallback(async () => {
    try {
      const docs = await listDocuments()
      setDocuments(docs)
      setSelectedIds((ids) => ids.filter((id) => docs.some((d) => d.doc_id === id)))
      setLoadError('')
    } catch (err) {
      setLoadError(err.message)
    }
  }, [])

  useEffect(() => {
    refreshDocuments()
  }, [refreshDocuments])

  const addMessage = (message) => {
    const id = nextId.current++
    setMessages((all) => [...all, { id, ...message }])
    return id
  }

  // Runs one backend call and shows its result (or its error) in the chat
  async function runTask(userText, call) {
    addMessage({ role: 'user', text: userText })
    setBusy(true)
    try {
      const result = await call()
      const id = addMessage({ role: 'assistant', kind: 'result', result })
      setActiveMessageId(id)
      setActiveN(null)
    } catch (err) {
      addMessage({ role: 'assistant', kind: 'error', text: err.message })
    } finally {
      setBusy(false)
    }
  }

  const toggle = (docId) =>
    setSelectedIds((ids) => (ids.includes(docId) ? ids.filter((id) => id !== docId) : [...ids, docId]))

  async function handleDelete(doc) {
    if (!window.confirm(`Delete "${doc.doc_name}" and all its indexed passages?`)) return
    try {
      await deleteDocument(doc.doc_id)
      await refreshDocuments()
    } catch (err) {
      addMessage({ role: 'assistant', kind: 'error', text: err.message })
    }
  }

  const activeMessage = messages.find((m) => m.id === activeMessageId)

  return (
    <div className="mx-auto max-w-[96rem] px-4 py-5">
      <header className="mb-5">
        <h1 className="text-2xl font-semibold tracking-tight">ResearchPilot</h1>
        <p className="text-sm text-stone-600">Ask your research papers questions. Every answer shows its evidence.</p>
      </header>

      {loadError && (
        <p role="alert" className="mb-4 rounded-lg border border-red-300 bg-red-50 px-3.5 py-2 text-sm text-red-800">
          {loadError}
        </p>
      )}

      <div className="grid gap-5 lg:h-[calc(100vh-9rem)] lg:grid-cols-[18rem_minmax(0,1fr)_24rem]">
        <aside className="space-y-4 overflow-y-auto">
          <UploadBox
            onUploaded={(result) => {
              refreshDocuments()
              setSelectedIds((ids) => (ids.includes(result.doc_id) ? ids : [...ids, result.doc_id]))
            }}
          />
          <section aria-label="Your papers">
            <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-stone-500">Your papers</h2>
            <DocumentList
              documents={documents}
              selectedIds={selectedIds}
              busy={busy}
              onToggle={toggle}
              onDelete={handleDelete}
              onSummarize={(doc) => runTask(`Summarize ${doc.doc_name}`, () => summarizeDocument(doc.doc_id))}
            />
          </section>
        </aside>

        <main className="min-w-0 rounded-2xl bg-stone-100/70 p-4">
          <Chat
            messages={messages}
            busy={busy}
            selectedCount={selectedIds.length}
            activeMessageId={activeMessageId}
            activeN={activeN}
            onAsk={(q) => runTask(q, () => askQuestion(q, selectedIds))}
            onCompare={(focus) =>
              runTask(`Compare selected papers: ${focus}`, () => compareDocuments(selectedIds, focus))
            }
            onCite={(messageId, n) => {
              setActiveMessageId(messageId)
              setActiveN(n)
            }}
          />
        </main>

        <aside className="overflow-y-auto" aria-label="Evidence">
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-stone-500">Evidence</h2>
          <EvidencePanel result={activeMessage?.result} activeN={activeN} />
        </aside>
      </div>
    </div>
  )
}