import { ref } from 'vue'
import { useStorage } from '~/composables/useStorage'

export const useUnits = () => {
  const { loadSettings, saveSettings } = useStorage()
  const settings = loadSettings()
  const unit = ref<'kg' | 'lbs'>(settings.unit)

  const toggleUnit = () => {
    unit.value = unit.value === 'kg' ? 'lbs' : 'kg'
    saveSettings({ unit: unit.value })
  }

  const formatWeight = (kg: number): string => {
    if (unit.value === 'lbs') {
      return `${Math.round(kg * 2.205).toLocaleString()} lbs`
    }
    return `${kg.toLocaleString()} kg`
  }

  return { unit, toggleUnit, formatWeight }
}
