/**
 * JWT token utilities for checking expiration.
 */

interface JWTPayload {
  exp?: number;
  sub?: string;
  [key: string]: any;
}

/**
 * Decode JWT token without verification (client-side only).
 * Note: This does NOT verify the signature, only decodes the payload.
 * For security, always verify tokens on the server side.
 */
export function decodeJWT(token: string): JWTPayload | null {
  try {
    const base64Url = token.split(".")[1];
    if (!base64Url) return null;
    
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    
    return JSON.parse(jsonPayload);
  } catch (e) {
    return null;
  }
}

/**
 * Check if JWT token is expired.
 */
export function isTokenExpired(token: string): boolean {
  const payload = decodeJWT(token);
  if (!payload || !payload.exp) {
    return true; // If we can't decode or no expiration, consider it expired
  }
  
  const expirationTime = payload.exp * 1000; // Convert to milliseconds
  const currentTime = Date.now();
  
  return currentTime >= expirationTime;
}

/**
 * Get token expiration time in milliseconds.
 */
export function getTokenExpirationTime(token: string): number | null {
  const payload = decodeJWT(token);
  if (!payload || !payload.exp) {
    return null;
  }
  
  return payload.exp * 1000; // Convert to milliseconds
}

