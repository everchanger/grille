import { describe, it, expect } from 'vitest'
import { resolveAssetUrl } from '~/utils/useAssetUrl'

describe('resolveAssetUrl', () => {
  it('prepends base URL to absolute paths', () => {
    const result = resolveAssetUrl('/cars/toyota-supra-a80.webp')
    // In test env, BASE_URL defaults to '/'
    expect(result).toBe('/cars/toyota-supra-a80.webp')
  })

  it('handles paths without leading slash', () => {
    const result = resolveAssetUrl('cars/toyota-supra-a80.webp')
    expect(result).toBe('/cars/toyota-supra-a80.webp')
  })

  it('handles empty path', () => {
    const result = resolveAssetUrl('')
    expect(result).toBe('/')
  })
})
