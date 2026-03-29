import type { Car } from '~/types'

export const carLabel = (car: Car): string => `${car.make} ${car.model} (${car.year})`
