import { describe, it, expect } from 'vitest'
import { carLabel } from '~/utils/carLabel'
import type { Car } from '~/types'

const makeCar = (overrides: Partial<Car> = {}): Car => ({
  id: 1,
  make: 'Toyota',
  model: 'Supra (A80)',
  year: 1993,
  country: 'Japan',
  horsepower: 320,
  weight_kg: 1560,
  engine: 'I6 Twin Turbo',
  drivetrain: 'RWD',
  image: '/cars/toyota-supra-a80.webp',
  fact: 'A great car.',
  wiki: 'https://en.wikipedia.org/wiki/Toyota_Supra',
  ...overrides,
})

describe('carLabel', () => {
  it('formats a car as "Make Model (Year)"', () => {
    const car = makeCar()
    expect(carLabel(car)).toBe('Toyota Supra (A80) (1993)')
  })

  it('handles different car data', () => {
    const car = makeCar({ make: 'Mazda', model: 'RX-7 (FD)', year: 1992 })
    expect(carLabel(car)).toBe('Mazda RX-7 (FD) (1992)')
  })

  it('handles car without parentheses in model', () => {
    const car = makeCar({ make: 'Ferrari', model: 'Testarossa', year: 1984 })
    expect(carLabel(car)).toBe('Ferrari Testarossa (1984)')
  })
})
