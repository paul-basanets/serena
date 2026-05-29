import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import ConfigCard from '../src/components/overview/ConfigCard.svelte';
import type { ResponseConfigOverview } from '../src/lib/api/types';

function makeConfig(over: Partial<ResponseConfigOverview> = {}): ResponseConfigOverview {
  return {
    active_project: { name: 'serena', language: 'Python', path: '/x' },
    context: { name: 'claude-code', description: '', path: '/ctx' },
    modes: [{ name: 'editing', path: '/m1' }],
    active_tools: ['find_symbol'],
    agent_interface: 'tools',
    language_backend: 'LSP',
    facades: null,
    tool_stats_summary: {},
    registered_projects: [],
    available_tools: [],
    available_modes: [],
    available_contexts: [],
    available_memories: [],
    jetbrains_mode: false,
    languages: ['python'],
    encoding: 'utf-8',
    current_client: 'claude',
    serena_version: '1.5.4',
    newer_serena_version: null,
    ...over,
  };
}

const cbs = {
  onaddlanguage: vi.fn(),
  onremovelanguage: vi.fn(),
  oneditconfig: vi.fn(),
  onopenmemory: vi.fn(),
  oncreatememory: vi.fn(),
  ondeletememory: vi.fn(),
};

describe('ConfigCard', () => {
  it('does not render a Client field', () => {
    render(ConfigCard, { props: { data: makeConfig(), ...cbs } });
    expect(screen.queryByText('Client')).toBeNull();
  });

  it('shows the backend and hides the languages in jetbrains mode', () => {
    render(ConfigCard, {
      props: { data: makeConfig({ jetbrains_mode: true, language_backend: 'JetBrains' }), ...cbs },
    });
    expect(screen.getByText('JetBrains')).toBeInTheDocument();
    expect(screen.queryByText('Languages')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Add Language' })).toBeNull();
  });

  it('counts only the enabled facade functions', () => {
    const facades = [
      {
        name: 'lsp',
        is_enabled: true,
        methods: [
          { name: 'find_symbol', is_enabled: true },
          { name: 'rename', is_enabled: false },
        ],
      },
      { name: 'jb', is_enabled: false, methods: [{ name: 'find_symbol', is_enabled: false }] },
    ];
    render(ConfigCard, {
      props: { data: makeConfig({ agent_interface: 'repl', facades }), ...cbs },
    });
    expect(screen.getByText('Active Functions (1)')).toBeInTheDocument();
  });

  it('shows Add Language when not in jetbrains mode', () => {
    render(ConfigCard, { props: { data: makeConfig(), ...cbs } });
    expect(screen.getByRole('button', { name: 'Add Language' })).toBeInTheDocument();
  });

  it('hides the newer-version badge when the backend reports none', () => {
    render(ConfigCard, { props: { data: makeConfig(), ...cbs } });
    expect(screen.queryByText(/newer version available/)).toBeNull();
  });

  it('links to the releases page when a newer version is available', () => {
    render(ConfigCard, { props: { data: makeConfig({ newer_serena_version: '1.6.2' }), ...cbs } });
    const link = screen.getByRole('link', { name: /newer version available: 1\.6\.2/ });
    expect(link).toHaveAttribute('href', 'https://github.com/oraios/serena/releases');
  });
});
