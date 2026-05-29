<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { theme } from '$lib/stores/theme.svelte';
  import {
    loadManifest,
    selectBanners,
    pickVariant,
    loadFragments,
    type LoadedBanner,
  } from '$lib/banners';

  let { target }: { target: 'platinum' | 'gold' } = $props();
  let banners = $state<LoadedBanner[]>([]);
  let idx = $state(0);
  let timer: ReturnType<typeof setInterval> | null = null;

  async function load() {
    banners = await loadFragments(selectBanners(await loadManifest(), target), target);
    if (banners.length) idx = Math.floor(Math.random() * banners.length);
    if (banners.length > 1) {
      timer = setInterval(() => {
        idx = (idx + 1) % banners.length;
      }, 6000);
    }
  }
  onMount(() => {
    void load();
  });
  onDestroy(() => {
    if (timer) clearInterval(timer);
  });

  const current = $derived(banners[idx]);
</script>

{#if current}
  <div class="banner {target}">
    <a href={current.link} target="_blank" rel="noopener noreferrer">
      {#if current.fragment !== undefined}
        <!-- eslint-disable-next-line svelte/no-at-html-tags -- fragment served by the banner manifest host, as in the legacy dashboard -->
        <div class="banner-html">{@html current.fragment}</div>
      {:else}
        <img src={pickVariant(current, theme.current)} alt={current.alt ?? ''} />
      {/if}
    </a>
  </div>
{/if}

<style>
  .banner {
    position: relative;
    display: inline-flex;
    align-items: center;
  }
  .banner.gold {
    display: flex;
    width: 100%;
  }
  .banner.gold a {
    display: block;
    width: 100%;
    color: inherit;
    text-decoration: none;
  }
  .banner-html {
    box-sizing: border-box;
    width: 100%;
    max-width: 400px;
    border-radius: var(--radius);
    background: var(--bg-card);
    color: var(--text-primary);
  }
  .banner img {
    max-height: 90px;
    display: block;
  }
  .banner.platinum img {
    max-height: 150px;
  }
  .banner.gold img {
    width: 100%;
    height: auto;
    max-height: none;
    display: block;
  }
</style>
