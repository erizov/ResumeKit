/**
 * API client with retry mechanism and offline detection.
 */

interface RetryOptions {
  maxRetries?: number;
  retryDelay?: number;
  retryableStatuses?: number[];
}

const DEFAULT_RETRY_OPTIONS: RetryOptions = {
  maxRetries: 3,
  retryDelay: 1000, // 1 second
  retryableStatuses: [408, 429, 500, 502, 503, 504],
};

/**
 * Check if the browser is online.
 */
export function isOnline(): boolean {
  return navigator.onLine;
}

/**
 * Fetch with retry mechanism and offline detection.
 */
export async function fetchWithRetry(
  url: string,
  options: RequestInit = {},
  retryOptions: RetryOptions = {}
): Promise<Response> {
  const config = { ...DEFAULT_RETRY_OPTIONS, ...retryOptions };
  let lastError: Error | null = null;

  // Check offline status
  if (!isOnline()) {
    throw new Error(
      "You are currently offline. Please check your internet connection."
    );
  }

  // Add auth token if available
  const token = localStorage.getItem("token");
  if (token) {
    options.headers = {
      ...options.headers,
      Authorization: `Bearer ${token}`,
    };
  }

  for (let attempt = 0; attempt <= config.maxRetries!; attempt++) {
    try {
      const response = await fetch(url, options);

      // If successful or non-retryable error, return immediately
      if (
        response.ok ||
        !config.retryableStatuses!.includes(response.status)
      ) {
        return response;
      }

      // If last attempt, return the error response
      if (attempt === config.maxRetries) {
        return response;
      }

      // Wait before retrying
      await new Promise((resolve) =>
        setTimeout(resolve, config.retryDelay! * (attempt + 1))
      );
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));

      // If last attempt, throw the error
      if (attempt === config.maxRetries) {
        throw lastError;
      }

      // Wait before retrying
      await new Promise((resolve) =>
        setTimeout(resolve, config.retryDelay! * (attempt + 1))
      );
    }
  }

  throw lastError || new Error("Request failed after retries");
}

/**
 * Get user-friendly error message from response.
 */
export async function getErrorMessage(
  response: Response
): Promise<string> {
  try {
    const data = await response.json();
    if (data.detail) {
      return data.detail;
    }
  } catch {
    // If JSON parsing fails, use status text
  }

  // Map status codes to user-friendly messages
  const statusMessages: Record<number, string> = {
    400: "Invalid request. Please check your input.",
    401: "Authentication required. Please log in.",
    403: "You don't have permission to perform this action.",
    404: "The requested resource was not found.",
    408: "Request timeout. Please try again.",
    429: "Too many requests. Please wait a moment and try again.",
    500: "Server error. Please try again later.",
    502: "Service temporarily unavailable. Please try again later.",
    503: "Service unavailable. Please try again later.",
    504: "Request timeout. Please try again.",
  };

  return (
    statusMessages[response.status] ||
    `Request failed with status ${response.status}`
  );
}

