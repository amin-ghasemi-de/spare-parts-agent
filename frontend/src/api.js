async function request(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })

  if (!response.ok) {
    let message = `Error ${response.status}`
    try {
      const data = await response.json()
      if (data.detail) {
        message = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)
      }
    } catch {
      // the error response had no JSON body
    }
    throw new Error(message)
  }

  return response.json()
}

export const api = {
  getSampleEmails: () => request('/sample-emails'),
  getCases: () => request('/cases'),
  getCase: (id) => request(`/cases/${id}`),
  createCase: (emailText) =>
    request('/cases', { method: 'POST', body: JSON.stringify({ email_text: emailText }) }),
  approveCase: (id, finalReply, note) =>
    request(`/cases/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify({ final_reply: finalReply, note }),
    }),
  rejectCase: (id, note) =>
    request(`/cases/${id}/reject`, { method: 'POST', body: JSON.stringify({ note }) }),
}