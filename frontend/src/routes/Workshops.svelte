<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '../lib/api';
  import { user } from '../lib/auth';
  import type { Workshop } from '../lib/types';

  let rows: Workshop[] = [];
  let error = '';
  let form = { name: '', site: '', notes: '' };
  let editingId: number | null = null;
  let busyId: number | null = null;

  const isAdmin = () => $user?.role === 'admin';

  async function load() {
    error = '';
    try {
      rows = await api<Workshop[]>('/workshops?includeArchived=1');
    } catch (e) {
      error = e instanceof Error ? e.message : '加载失败';
    }
  }

  onMount(load);

  function reset() {
    form = { name: '', site: '', notes: '' };
    editingId = null;
  }

  function edit(row: Workshop) {
    editingId = row.id;
    form = {
      name: row.name || '',
      site: row.site || '',
      notes: row.notes || '',
    };
  }

  async function save() {
    error = '';
    try {
      if (editingId) {
        await api(`/workshops/${editingId}`, {
          method: 'PUT',
          body: JSON.stringify(form),
        });
      } else {
        await api('/workshops', {
          method: 'POST',
          body: JSON.stringify(form),
        });
      }
      reset();
      await load();
    } catch (e) {
      error = e instanceof Error ? e.message : '保存失败';
    }
  }

  async function setArchived(row: Workshop, archived: boolean) {
    const action = archived ? '归档' : '解档';
    const tip = archived
      ? '归档后该车间及其研磨机的历史数据仍可查看，但禁止新增机台、取样与遍次。'
      : '解档后该车间恢复新建机台、取样与遍次。';
    if (!confirm(`确认${action}车间「${row.name}」？${tip}`)) return;

    error = '';
    busyId = row.id;
    try {
      await api(`/workshops/${row.id}/${archived ? 'archive' : 'unarchive'}`, {
        method: 'POST',
      });
      await load();
    } catch (e) {
      error = e instanceof Error ? e.message : `${action}失败`;
    } finally {
      busyId = null;
    }
  }
</script>

<header class="page-head">
  <h1>车间</h1>
  <p>油墨研磨车间基础信息（非仓库库存）；车间只归档不删除，归档不影响历史台账查看</p>
</header>

{#if error}
  <div class="err">{error}</div>
{/if}

<section class="panel">
  <h2>{editingId ? '编辑车间' : '新增车间'}</h2>
  <div class="fields">
    <div class="field"><label>名称<input bind:value={form.name} /></label></div>
    <div class="field"><label>厂区/位置<input bind:value={form.site} /></label></div>
    <div class="field full"><label>备注<textarea rows="2" bind:value={form.notes} /></label></div>
  </div>
  <div class="actions">
    <button class="btn-primary" on:click={save}>{editingId ? '保存' : '创建'}</button>
    {#if editingId}
      <button class="btn-ghost" on:click={reset}>取消</button>
    {/if}
  </div>
</section>

<section class="panel">
  <table class="data-table">
    <thead>
      <tr>
        <th>ID</th>
        <th>名称</th>
        <th>位置</th>
        <th>备注</th>
        <th>状态</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      {#each rows as row}
        <tr class:archived={row.archived}>
          <td>{row.id}</td>
          <td>{row.name}</td>
          <td>{row.site || '—'}</td>
          <td>{row.notes || '—'}</td>
          <td>
            {#if row.archived}
              <span class="badge archived">已归档</span>
            {:else}
              <span class="badge active">启用中</span>
            {/if}
          </td>
          <td class="ops">
            <button class="link-btn" on:click={() => edit(row)}>编辑</button>
            {#if isAdmin()}
              {#if row.archived}
                <button
                  class="link-btn"
                  disabled={busyId === row.id}
                  on:click={() => setArchived(row, false)}
                >解档</button>
              {:else}
                <button
                  class="link-btn danger"
                  disabled={busyId === row.id}
                  on:click={() => setArchived(row, true)}
                >归档</button>
              {/if}
            {/if}
          </td>
        </tr>
      {:else}
        <tr><td colspan="6">暂无数据</td></tr>
      {/each}
    </tbody>
  </table>
</section>

<style>
  tr.archived td {
    opacity: 0.6;
  }

  .badge.archived {
    background: rgba(120, 120, 120, 0.18);
    color: var(--steel);
    border: 1px solid var(--line);
  }

  .badge.active {
    background: rgba(60, 120, 90, 0.18);
    color: #7fc79a;
    border: 1px solid rgba(60, 120, 90, 0.4);
  }
</style>
