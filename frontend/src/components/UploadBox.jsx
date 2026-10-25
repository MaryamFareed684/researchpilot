import { useRef, useState } from 'react'
import { uploadDocument } from '../api.js'

const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`

export default function UploadBox({ onUploaded }) {
  const inputRef = useRef(null)
  const [state, setState] = useState({ busy: false, message: '', error: false })

  async function handleFile(event) {
    const file = event.target.files?.[0]
    event.target.value = '' // lets you pick the same file again later
    if (!file) return
    setState({ busy: true, message: `Reading and indexing ${file.name}... the first upload can take a minute.`, error: false })
    try {
      const result = await uploadDocument(file)
      setState({
        busy: false,
        message: result.already_indexed
          ? `${result.doc_name} was already indexed.`
          : `Indexed ${result.doc_name}: ${plural(result.total_pages, 'page')}, ${plural(result.chunks_indexed, 'passage')}.`,
        error: false,
      })
      onUploaded(result)
    } catch (err) {
      setState({ busy: false, message: err.message, error: true })
    }
  }

  return (
    <div>
      <input ref={inputRef} type="file" accept="application/pdf,.pdf" onChange={handleFile} className="hidden" />
      <button
        type="button"
        disabled={state.busy}
        onClick={() => inputRef.current?.click()}
        className="w-full rounded-lg border-2 border-dashed border-stone-300 bg-white px-3 py-4 text-sm font-medium text-stone-700 hover:border-teal-600 hover:text-teal-800 disabled:cursor-wait disabled:opacity-60"
      >
        {state.busy ? 'Working...' : 'Upload a PDF'}
      </button>
      {state.message && (
        <p role="status" className={`mt-2 text-xs ${state.error ? 'text-red-700' : 'text-stone-600'}`}>
          {state.message}
        </p>
      )}
    </div>
  )
}