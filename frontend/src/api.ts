export type ProcessMode = 'merge' | 'combine'

export async function processDocuments(
  mode: ProcessMode,
  files: File[],
): Promise<{ blob: Blob; filename: string }> {
  const form = new FormData()
  form.append('mode', mode)
  for (const file of files) {
    form.append('files', file)
  }

  const response = await fetch('/api/process', {
    method: 'POST',
    body: form,
  })

  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try {
      const body = (await response.json()) as { detail?: string | { msg: string }[] }
      if (typeof body.detail === 'string') {
        message = body.detail
      } else if (Array.isArray(body.detail)) {
        message = body.detail.map((d) => d.msg).join('; ')
      }
    } catch {
      /* keep default */
    }
    throw new Error(message)
  }

  const blob = await response.blob()
  const disposition = response.headers.get('Content-Disposition') ?? ''
  const match = disposition.match(/filename="?([^";]+)"?/)
  const filename = match?.[1] ?? (mode === 'merge' ? 'merged.docx' : 'combined.docx')

  return { blob, filename }
}
