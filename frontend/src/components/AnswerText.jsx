// A tiny, safe renderer for the model's answer.
// It builds React elements from plain text, so nothing from the model is ever
// inserted as HTML. It understands: ## headings, - bullets, **bold** and [1] citations.

const TOKEN = /(\*\*[^*]+\*\*|\[\d+(?:\s*,\s*\d+)*\])/g

function Inline({ text, onCite }) {
  return text
    .split(TOKEN)
    .filter(Boolean)
    .map((part, i) => {
      if (part.length > 4 && part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i}>{part.slice(2, -2)}</strong>
      }
      const citation = part.match(/^\[(\d+(?:\s*,\s*\d+)*)\]$/)
      if (citation) {
        return citation[1].split(',').map((n) => {
          const number = Number(n)
          return (
            <button
              key={`${i}-${number}`}
              type="button"
              onClick={() => onCite?.(number)}
              className="mx-0.5 rounded bg-teal-50 px-1 text-xs font-semibold text-teal-800 ring-1 ring-teal-300 hover:bg-teal-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-600"
              aria-label={`Show source ${number}`}
            >
              [{number}]
            </button>
          )
        })
      }
      return <span key={i}>{part}</span>
    })
}

function toBlocks(text) {
  const blocks = []
  let list = null
  for (const raw of text.split('\n')) {
    const line = raw.trim()
    if (!line) {
      list = null
      continue
    }
    const bullet = line.match(/^[-*•]\s+(.*)$/)
    if (bullet) {
      if (!list) {
        list = { type: 'list', items: [] }
        blocks.push(list)
      }
      list.items.push(bullet[1])
      continue
    }
    list = null
    const heading = line.match(/^#{1,6}\s+(.*)$/)
    blocks.push(heading ? { type: 'heading', text: heading[1] } : { type: 'paragraph', text: line })
  }
  return blocks
}

export default function AnswerText({ text, onCite }) {
  return (
    <div className="space-y-2 leading-relaxed">
      {toBlocks(text).map((block, i) => {
        if (block.type === 'heading') {
          return (
            <h3 key={i} className="pt-1 text-sm font-semibold uppercase tracking-wide text-stone-600">
              <Inline text={block.text} onCite={onCite} />
            </h3>
          )
        }
        if (block.type === 'list') {
          return (
            <ul key={i} className="list-disc space-y-1 pl-5">
              {block.items.map((item, j) => (
                <li key={j}>
                  <Inline text={item} onCite={onCite} />
                </li>
              ))}
            </ul>
          )
        }
        return (
          <p key={i}>
            <Inline text={block.text} onCite={onCite} />
          </p>
        )
      })}
    </div>
  )
}