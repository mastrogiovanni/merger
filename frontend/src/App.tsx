import { useCallback, useRef, useState } from 'react'
import { processDocuments, type ProcessMode } from './api'
import './App.css'

type DocEntry = {
  id: string
  file: File
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function App() {
  const [mode, setMode] = useState<ProcessMode>('merge')
  const [documents, setDocuments] = useState<DocEntry[]>([])
  const [dragOver, setDragOver] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<{ url: string; filename: string } | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const revokeResult = useCallback(() => {
    setResult((prev) => {
      if (prev) URL.revokeObjectURL(prev.url)
      return null
    })
  }, [])

  const addFiles = useCallback(
    (incoming: FileList | File[]) => {
      const accepted = Array.from(incoming).filter((f) =>
        f.name.toLowerCase().endsWith('.docx'),
      )
      if (accepted.length === 0 && incoming.length > 0) {
        setError('Only .docx files are supported.')
        return
      }
      setError(null)
      revokeResult()
      setDocuments((prev) => [
        ...prev,
        ...accepted.map((file) => ({
          id: crypto.randomUUID(),
          file,
        })),
      ])
    },
    [revokeResult],
  )

  const removeDoc = (id: string) => {
    revokeResult()
    setDocuments((prev) => prev.filter((d) => d.id !== id))
  }

  const moveDoc = (index: number, direction: -1 | 1) => {
    const next = index + direction
    if (next < 0 || next >= documents.length) return
    revokeResult()
    setDocuments((prev) => {
      const copy = [...prev]
      const [item] = copy.splice(index, 1)
      copy.splice(next, 0, item)
      return copy
    })
  }

  const clearAll = () => {
    revokeResult()
    setDocuments([])
    setError(null)
  }

  const handleProcess = async () => {
    if (documents.length < 2) {
      setError('Add at least two Word documents.')
      return
    }
    setLoading(true)
    setError(null)
    revokeResult()
    try {
      const { blob, filename } = await processDocuments(
        mode,
        documents.map((d) => d.file),
      )
      const url = URL.createObjectURL(blob)
      setResult({ url, filename })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    if (e.dataTransfer.files.length) addFiles(e.dataTransfer.files)
  }

  return (
    <div className="app">
      <header className="header">
        <div className="logo" aria-hidden>
          N
        </div>
        <h1>Merge Word documents</h1>
        <p>
          Upload multiple .docx files, choose merge or combine mode, and download
          a single document in the order you set.
        </p>
      </header>

      <section className="card" aria-labelledby="mode-label">
        <h2 id="mode-label" className="card-title">
          Processing mode
        </h2>
        <div className="mode-grid" role="radiogroup" aria-label="Processing mode">
          <label className="mode-option">
            <input
              type="radio"
              name="mode"
              value="merge"
              checked={mode === 'merge'}
              onChange={() => {
                setMode('merge')
                revokeResult()
              }}
            />
            <span className="mode-content">
              <strong>Merge (append)</strong>
              <span>
                Stitches files end-to-end. Best when layout is the same across
                documents.
              </span>
            </span>
          </label>
          <label className="mode-option">
            <input
              type="radio"
              name="mode"
              value="combine"
              checked={mode === 'combine'}
              onChange={() => {
                setMode('combine')
                revokeResult()
              }}
            />
            <span className="mode-content">
              <strong>Combine (sections)</strong>
              <span>
                Inserts section breaks and keeps each file&apos;s page setup and
                headers.
              </span>
            </span>
          </label>
        </div>
      </section>

      <section className="card" aria-labelledby="files-label">
        <h2 id="files-label" className="card-title">
          Documents ({documents.length})
        </h2>

        <div
          className={`dropzone${dragOver ? ' drag-over' : ''}`}
          onDragOver={(e) => {
            e.preventDefault()
            setDragOver(true)
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault()
              inputRef.current?.click()
            }
          }}
          role="button"
          tabIndex={0}
          aria-label="Upload Word documents"
        >
          <div className="dropzone-icon" aria-hidden>
            📄
          </div>
          <p>Drop .docx files here or click to browse</p>
          <small>Add as many files as you need — order matters</small>
        </div>

        <input
          ref={inputRef}
          type="file"
          accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          multiple
          onChange={(e) => {
            if (e.target.files?.length) addFiles(e.target.files)
            e.target.value = ''
          }}
        />

        {documents.length > 0 ? (
          <ul className="file-list">
            {documents.map((doc, index) => (
              <li key={doc.id} className="file-item">
                <span className="file-order">{index + 1}</span>
                <span className="file-name" title={doc.file.name}>
                  {doc.file.name}
                </span>
                <span className="file-size">{formatSize(doc.file.size)}</span>
                <div className="file-actions">
                  <button
                    type="button"
                    className="icon-btn"
                    aria-label={`Move ${doc.file.name} up`}
                    disabled={index === 0}
                    onClick={(e) => {
                      e.stopPropagation()
                      moveDoc(index, -1)
                    }}
                  >
                    ↑
                  </button>
                  <button
                    type="button"
                    className="icon-btn"
                    aria-label={`Move ${doc.file.name} down`}
                    disabled={index === documents.length - 1}
                    onClick={(e) => {
                      e.stopPropagation()
                      moveDoc(index, 1)
                    }}
                  >
                    ↓
                  </button>
                  <button
                    type="button"
                    className="icon-btn danger"
                    aria-label={`Remove ${doc.file.name}`}
                    onClick={(e) => {
                      e.stopPropagation()
                      removeDoc(doc.id)
                    }}
                  >
                    ×
                  </button>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="empty-hint">No files yet — upload at least two to continue.</p>
        )}
      </section>

      <div className="actions">
        <button
          type="button"
          className="primary-btn"
          disabled={loading || documents.length < 2}
          onClick={handleProcess}
        >
          {loading ? (
            <>
              <span className="spinner" aria-hidden />
              Processing…
            </>
          ) : mode === 'merge' ? (
            'Merge documents'
          ) : (
            'Combine documents'
          )}
        </button>
        {documents.length > 0 && (
          <button type="button" className="secondary-btn" onClick={clearAll}>
            Clear all files
          </button>
        )}
      </div>

      {error && (
        <div className="alert alert-error" role="alert">
          {error}
        </div>
      )}

      {result && (
        <div className="result-card">
          <p>
            Your {mode === 'merge' ? 'merged' : 'combined'} document is ready (
            {result.filename}).
          </p>
          <a className="download-btn" href={result.url} download={result.filename}>
            Download
          </a>
        </div>
      )}
    </div>
  )
}

export default App
