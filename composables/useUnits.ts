import { ref } from 'vue'
import type { Ref } from 'vue'
import { useStorage } from '~/composables/useStorage'

const KG_TO_LBS = 2.205

let _unit: Ref<'kg' | 'lbs'> | null = null

const getUnit = (): Ref<'kg' | 'lbs'> => {
  if (!_unit) {
    const { loadSettings } = useStorage()
    const settings = loadSettings()
    _unit = ref<'kg' | 'lbs'>(settings.unit)
  }
  return _unit
}

export const useUnits = () => {
  const unit = getUnit()
  const { saveSettings } = useStorage()

  const toggleUnit = () => {
    unit.value = unit.value === 'kg' ? 'lbs' : 'kg'
    saveSettings({ unit: unit.value })
  }

  const formatWeight = (kg: number): string => {
    if (unit.value === 'lbs') {
      return `${Math.round(kg * KG_TO_LBS).toLocaleString()} lbs`
    }
    return `${kg.toLocaleString()} kg`
  }

  return { unit, toggleUnit, formatWeight }
}
