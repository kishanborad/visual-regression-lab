import type { Scenario } from '../types';

export const PRESETS: Scenario[] = [
  {
    id: 'button-shift',
    name: 'Button Shift',
    description: 'Login form where the submit button shifts 3px right + 2px down',
    teaches: 'Catches layout drift from padding/margin changes',
    mutationClass: 'button-shift',
  },
  {
    id: 'color-swap',
    name: 'Color Swap',
    description: 'Pricing card where the CTA button color and header text change subtly',
    teaches: 'Subtle color regressions that pass code review but fail visual checks',
    mutationClass: 'color-swap',
  },
  {
    id: 'missing-element',
    name: 'Missing Element',
    description: 'Dashboard card where the progress bar disappears',
    teaches: 'Component removal or conditional rendering bugs',
    mutationClass: 'missing-element',
  },
  {
    id: 'font-change',
    name: 'Font Change',
    description: 'Blog preview where the title font changes from Poppins 700 to Inter 600',
    teaches: 'Typography regressions from font loading or CSS specificity',
    mutationClass: 'font-change',
  },
  {
    id: 'spacing-collapse',
    name: 'Spacing Collapse',
    description: 'Settings page where section gaps shrink and a divider disappears',
    teaches: 'Margin collapse and spacing regressions',
    mutationClass: 'spacing-collapse',
  },
];

export function getPreset(id: string): Scenario {
  return PRESETS.find((p) => p.id === id) ?? PRESETS[0];
}
