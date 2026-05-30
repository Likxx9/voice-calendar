<template>
  <component :is="currentLayout" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSettingsStore } from '@/stores/useSettingsStore'
import DefaultLayout from '@/layouts/DefaultLayout.vue'
import EyesFreeLayout from '@/layouts/EyesFreeLayout.vue'

const settingsStore = useSettingsStore()

const currentLayout = computed(() => {
  return settingsStore.settings.layout_mode === 'eyes-free' 
    ? EyesFreeLayout 
    : DefaultLayout
})
</script>
