<script setup lang="ts">
import { computed } from "vue";
import { RouterLink } from "vue-router";

const props = withDefaults(
  defineProps<{
    variant?: "primary" | "secondary" | "icon";
    to?: string;
    disabled?: boolean;
    type?: "button" | "submit" | "reset";
  }>(),
  {
    variant: "primary",
    disabled: false,
    type: "button",
  }
);

const componentType = computed(() => (props.to ? RouterLink : "button"));

const buttonClass = computed(() => {
  const classes = ["app-button"];
  if (props.variant === "primary") classes.push("primary-action");
  if (props.variant === "secondary") classes.push("secondary-action");
  if (props.variant === "icon") classes.push("icon-button");
  if (props.disabled) classes.push("is-disabled");
  return classes;
});
</script>

<template>
  <component
    :is="componentType"
    :to="to"
    :type="!to ? type : undefined"
    :class="buttonClass"
    :disabled="!to && disabled ? true : undefined"
    :aria-disabled="to && disabled ? true : undefined"
    :tabindex="to && disabled ? -1 : undefined"
  >
    <slot></slot>
  </component>
</template>
