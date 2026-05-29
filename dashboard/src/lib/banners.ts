import type { Theme } from './stores/theme.svelte';

/**
 * A single banner entry as returned by the remote manifest.
 * Field names mirror the legacy manifest:
 *   `image`      — light-mode image URL (present unless `html` is given)
 *   `image_dark` — optional dark-mode image URL; falls back to `image`
 *   `html`       — URL of an HTML fragment shown instead of an image (gold tier only)
 *   `link`       — click-through URL
 *   `alt`        — alt text
 */
export interface BannerEntry {
  image?: string;
  image_dark?: string;
  html?: string;
  link: string;
  alt?: string;
}

/** A banner ready to render; `fragment` holds the loaded markup of an HTML banner. */
export interface LoadedBanner extends BannerEntry {
  fragment?: string;
}

/**
 * Top-level manifest shape: banners are keyed by sponsorship tier.
 */
export interface BannerManifest {
  platinum?: BannerEntry[];
  gold?: BannerEntry[];
}

/** Switch to load banners from a local test server instead of production. */
const IS_TEST_ENV = false;
const BANNER_BASE_URL = IS_TEST_ENV
  ? 'http://localhost:8090/oraios-software/serena-banners'
  : 'https://oraios-software.de/serena-banners';
export const BANNER_MANIFEST_URL = `${BANNER_BASE_URL}/manifest.php`;

/** Return the banners for the given tier (empty array if the key is missing). */
export function selectBanners(
  manifest: BannerManifest,
  target: 'platinum' | 'gold',
): BannerEntry[] {
  return manifest[target] ?? [];
}

/** Pick the theme-appropriate image, falling back to the light image. */
export function pickVariant(entry: BannerEntry, theme: Theme): string | undefined {
  return theme === 'dark' ? (entry.image_dark ?? entry.image) : entry.image;
}

/** Fetch the manifest; resilient — returns an empty manifest on any failure. */
export async function loadManifest(): Promise<BannerManifest> {
  try {
    const res = await fetch(BANNER_MANIFEST_URL);
    if (!res.ok) return {};
    return (await res.json()) as BannerManifest;
  } catch {
    return {};
  }
}

/**
 * Load the fragments of HTML banners, keeping manifest order. Drops HTML banners
 * outside the gold tier and those whose fragment fails to load.
 */
export async function loadFragments(
  banners: BannerEntry[],
  target: 'platinum' | 'gold',
): Promise<LoadedBanner[]> {
  const loaded = await Promise.all(
    banners.map(async (banner): Promise<LoadedBanner | null> => {
      if (!banner.html) return banner;
      if (target !== 'gold') {
        console.error('HTML banners are only supported for gold banners:', banner.html);
        return null;
      }
      try {
        const res = await fetch(banner.html);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return { ...banner, fragment: await res.text() };
      } catch (error) {
        console.error('Error loading HTML banner:', banner.html, error);
        return null;
      }
    }),
  );
  return loaded.filter((b) => b !== null);
}
