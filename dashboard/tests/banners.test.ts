import { describe, it, expect, vi } from 'vitest';
import { selectBanners, pickVariant, loadFragments } from '../src/lib/banners';

const manifest = {
  platinum: [{ image: 'p-l.png', image_dark: 'p-d.png', link: 'https://a', alt: 'A' }],
  gold: [
    { image: 'g-l.png', image_dark: 'g-d.png', link: 'https://b', alt: 'B' },
    { image: 'g2-l.png', link: 'https://c', alt: 'C' },
  ],
};

describe('banners', () => {
  it('filters by target', () => {
    expect(selectBanners(manifest, 'gold')).toHaveLength(2);
    expect(selectBanners(manifest, 'platinum')).toHaveLength(1);
    expect(selectBanners(manifest, 'platinum')[0].link).toBe('https://a');
  });

  it('picks the variant for the theme', () => {
    const b = selectBanners(manifest, 'platinum')[0];
    expect(pickVariant(b, 'dark')).toBe('p-d.png');
    expect(pickVariant(b, 'light')).toBe('p-l.png');
  });

  it('falls back to the light image when no dark variant exists', () => {
    const b = selectBanners(manifest, 'gold')[1];
    expect(pickVariant(b, 'dark')).toBe('g2-l.png');
    expect(pickVariant(b, 'light')).toBe('g2-l.png');
  });

  it('tolerates a missing target array', () => {
    expect(selectBanners({} as never, 'gold')).toEqual([]);
  });

  it('loads gold HTML fragments in manifest order and drops the ones that cannot be shown', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) =>
        url === 'ok.html' ? new Response('<b>hi</b>') : new Response('', { status: 404 }),
      ),
    );
    const banners = [
      { html: 'ok.html', link: 'https://a' },
      { image: 'i.png', link: 'https://b' },
      { html: 'missing.html', link: 'https://c' },
    ];

    expect(await loadFragments(banners, 'gold')).toEqual([
      { html: 'ok.html', link: 'https://a', fragment: '<b>hi</b>' },
      { image: 'i.png', link: 'https://b' },
    ]);
    expect(await loadFragments(banners, 'platinum')).toEqual([
      { image: 'i.png', link: 'https://b' },
    ]);
  });
});
