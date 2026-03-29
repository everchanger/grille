import { ref } from 'vue'
import { useStorage } from '~/composables/useStorage'

const KG_TO_LBS = 2.205

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
      return `${Math.round(kg * KG_TO_LBS).toLocaleString()} lbs`
    }
    return `${kg.toLocaleString()} kg`
  }

  return { unit, toggleUnit, formatWeight }
}
