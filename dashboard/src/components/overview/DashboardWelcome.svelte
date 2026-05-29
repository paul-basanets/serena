<script lang="ts">
  import { saveWebDashboardOpenOnLaunch } from '$lib/api/endpoints';
  import { runMutation } from '$lib/api/mutation';
  import Button from '../common/Button.svelte';
  import Card from '../common/Card.svelte';
  // hides the pane until the config poll reflects the saved choice
  let dismissed = $state(false);
  let error = $state<string | null>(null);
  async function choose(value: boolean) {
    dismissed = true;
    const res = await runMutation(() => saveWebDashboardOpenOnLaunch(value));
    if (!res.ok) {
      dismissed = false;
      error = res.message ?? 'Could not queue the preference change.';
    }
  }
</script>

{#if !dismissed}
  <Card title="Welcome to the Serena Dashboard">
    <div class="welcome">
      <p>
        The dashboard lets you inspect Serena's current configuration, monitor tool usage and
        running tasks, view logs, and manage project memories.
      </p>
      <p>
        We opened the dashboard automatically to introduce you to its features. Please choose
        whether it should continue to open whenever Serena starts.
      </p>
      <p>If you disable automatic opening, you can still open the dashboard:</p>
      <ul>
        <li>via the Serena tray icon (on supported platforms)</li>
        <li>
          by telling your agent to &ldquo;open the Serena dashboard&rdquo; (on other platforms)
        </li>
      </ul>
      {#if error}<p class="error" role="alert">{error}</p>{/if}
      <div class="actions">
        <Button onclick={() => choose(true)}>Open this whenever Serena starts</Button>
        <Button variant="secondary" onclick={() => choose(false)}>Disable automatic opening</Button>
      </div>
    </div>
  </Card>
{/if}

<style>
  .welcome p,
  .welcome ul {
    margin: 0 0 var(--space-4);
    line-height: 1.6;
  }
  .welcome ul {
    padding-left: var(--space-5);
  }
  .error {
    color: var(--log-error);
  }
  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-2);
  }
</style>
