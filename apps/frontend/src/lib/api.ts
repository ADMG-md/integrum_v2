const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"
const TIMEOUT_MS = 30000;
const MAX_RETRIES = 3;

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
    this.name = "ApiError"
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  retries = 0
): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }

  try {
    const res = await fetch(`${API_URL}${path}`, {
      ...options,
      headers,
      signal: controller.signal
    })

    clearTimeout(timeoutId);

    if (!res.ok) {
      const body = await res.text().catch(() => "")
      throw new ApiError(res.status, body || res.statusText)
    }

    const text = await res.text()
    if (!text) return undefined as T
    return JSON.parse(text) as T
  } catch (error: unknown) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error(`Request timeout after ${TIMEOUT_MS}ms`);
    }
    
    if (retries < MAX_RETRIES && (error instanceof Error && (error.name === 'TypeError' || (error instanceof ApiError && error.status >= 500)))) {
        await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, retries))); // Exponential backoff
        return request<T>(path, options, retries + 1);
    }
    throw error;
  }
}

export const api = {
  get: <T>(path: string) => request<T>(path, { method: "GET" }),
  post: <T, B = unknown>(path: string, body?: B) =>
    request<T>(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),
  patch: <T, B = unknown>(path: string, body?: B) =>
    request<T>(path, {
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
    }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  uploadFile: async <T>(path: string, formData: FormData): Promise<T> => {
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null
    const headers: Record<string, string> = {}
    if (token) headers["Authorization"] = `Bearer ${token}`

    const res = await fetch(`${API_URL}${path}`, { method: "POST", headers, body: formData })
    if (!res.ok) {
      const body = await res.text().catch(() => "")
      throw new ApiError(res.status, body || res.statusText)
    }
    const text = await res.text()
    if (!text) return undefined as T
    return JSON.parse(text) as T
  },
}

export { ApiError }
