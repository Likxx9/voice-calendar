<template>
  <span class="entity-hl" :class="`entity-hl--${type}`" :title="tooltip">
    <slot>{{ text }}</slot>
  </span>
</template>

<script setup lang="ts">

const props = withDefaults(defineProps<{
  text?: string
  type?: 'time' | 'location' | 'person' | 'title' | 'general'
  tooltip?: string
}>(), {
  text: '',
  type: 'general',
  tooltip: '',
})
</script>

<style scoped>
.entity-hl {
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: var(--vc-weight-medium);
  border-bottom: 2px solid;
  transition: background var(--vc-transition-fast);
}

.entity-hl--time {
  color: var(--vc-primary-light);
  background: hsla(224, 76%, 48%, 0.1);
  border-color: var(--vc-primary);
}
.entity-hl--location {
  color: var(--vc-success);
  background: var(--vc-success-soft);
  border-color: var(--vc-success);
}
.entity-hl--person {
  color: var(--vc-accent-light);
  background: hsla(270, 72%, 56%, 0.1);
  border-color: var(--vc-accent);
}
.entity-hl--title {
  color: var(--vc-warning);
  background: var(--vc-warning-soft);
  border-color: var(--vc-warning);
}
.entity-hl--general {
  color: var(--vc-text-secondary);
  background: var(--vc-bg-elevated);
  border-color: var(--vc-border);
}
</style>
