import { describe, it, expect } from 'vitest';
import { render, fireEvent, screen } from '@testing-library/svelte';
import DashboardWelcome from '../src/components/overview/DashboardWelcome.svelte';
import { stubFetchJson, errBody, okBody } from './helpers';

describe('DashboardWelcome', () => {
  it('posts the choice and hides itself', async () => {
    const fetch = stubFetchJson(okBody());
    render(DashboardWelcome);
    await fireEvent.click(screen.getByRole('button', { name: 'Disable automatic opening' }));
    const [url, init] = fetch.mock.calls[0];
    expect(String(url)).toContain('/save_web_dashboard_open_on_launch');
    expect(JSON.parse(init.body)).toEqual({ web_dashboard_open_on_launch: false });
    expect(screen.queryByText('Welcome to the Serena Dashboard')).not.toBeInTheDocument();
  });

  it('stays visible and shows the error when saving fails', async () => {
    stubFetchJson(errBody('cannot save'));
    render(DashboardWelcome);
    await fireEvent.click(screen.getByRole('button', { name: 'Open this whenever Serena starts' }));
    expect(await screen.findByText('cannot save')).toBeInTheDocument();
  });
});
