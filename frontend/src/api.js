// Every call to the backend lives in this file.
// The backend address comes from one setting, so deploying means changing one line.
const BASE = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(`${BASE}${path}`, options)
  } catch {
    throw new Error('Cannot reach the server. Is the backend running?')
  }

  let data = null
  try {
    data = await response.json()
  } catch {
    // the response had no JSON body
  }

  if (!response.ok) {
    const detail = data?.detail
    if (typeof detail === 'string') throw new Error(detail)
    if (Array.isArray(detail) && detail[0]?.msg) throw new Error(`Please check your input: ${detail[0].msg}`)
    throw new Error(`Something went wrong (error ${response.status}).`)
  }
  return data
}

const jsonPost = (body) => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})

export const listDocuments = () => request('/documents').then((data) => data.documents)

export function uploadDocument(file) {
  const form = new FormData()
  form.append('file', file)
  return request('/upload', { method: 'POST', body: form })
}

export const deleteDocument = (docId) => request(`/documents/${docId}`, { method: 'DELETE' })

export const askQuestion = (question, docIds) =>
  request('/ask', jsonPost({ question, doc_ids: docIds.length ? docIds : null }))

export const summarizeDocument = (docId) => request('/summarize', jsonPost({ doc_id: docId }))

export const compareDocuments = (docIds, focus) => request('/compare', jsonPost({ doc_ids: docIds, focus }))