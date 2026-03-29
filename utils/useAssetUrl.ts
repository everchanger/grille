/**
 * Resolves a public asset path by prepending the app's baseURL.
 * In production on GitHub Pages (baseURL: '/grille/'), an image path like
 * '/cars/foo.webp' needs to become '/grille/cars/foo.webp'.
 */
export const resolveAssetUrl = (path: string): string => {
  const base = import.meta.env.BASE_URL || '/'
  const cleanBase = base.endsWith('/') ? base : `${base}/`
  const cleanPath = path.startsWith('/') ? path.slice(1) : path
  return `${cleanBase}${cleanPath}`
}
