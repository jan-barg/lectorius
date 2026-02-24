/**
 * Convert a 0-100 slider value to a perceptual audio volume.
 * Uses a quadratic curve so low slider values feel quieter and
 * the perceived loudness scales more naturally.
 *
 * @param slider - Slider value 0-100
 * @param cap - Maximum output volume (default 1.0)
 */
export function toPerceptualVolume(slider: number, cap: number = 1.0): number {
	return Math.pow(slider / 100, 2) * cap;
}
