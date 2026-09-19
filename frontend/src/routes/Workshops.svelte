<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '../lib/api';
  import type { Workshop } from '../lib/types';

  let rows: Workshop[] = [];
  let error = '';
  let notice = '';
  let showArchived = false;
  let form = { name: '', site: '', notes: '' };
  let editingId: number | null = null;

  async function load() {
    error = '';
    try {
      rows = await api<Workshop[]>(showArchived ? '/workshops?includeArchived=1' : '/workshops');
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
    notice = '';
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

  async function archive(row: Workshop) {
    if (!confirm(`确认归档车间「${row.name}」？归档后该车间将禁止新建写入，历史数据保留。`)) return;
    error = '';
    notice = '';
    try {
      const res = await api<Workshop & { millCount: number }>(`/workshops/${row.id}/archive`, {
        method: 'POST',
      });
      notice = `车间「${row.name}」已归档（含 ${res.millCount} 台研磨机）`;
      await load();
    } catch (e) {
      error = e instanceof Error ? e.message : '归档失败';
    }
  }

  async function unarchive(row: Workshop) {
    error = '';
    notice = '';
    try {
      await api(`/workshops/${row.id}/unarchive`, { method: 'POST' });
      notice = `车间「${row.name}」已解档，恢复写入`;
      await load();
    } catch (e) {
      error = e instanceof Error ? e.message : '解档失败';
    }
  }
</script>

<header class="page-head">
  <h1>车间</h1>
  <p>油墨研磨车间基础信息（非仓库库存）；归档为软删除，不物理删除数据</p>
</header>

{#if error}
  <div class="err">{error}</div>
{/if}
{#if notice}
  <div class="notice">{notice}</div>
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
  <div class="list-head">
    <label class="toggle">
      <input type="checkbox" bind:checked={showArchived} on:change={load} />
      显示已归档车间
    </label>
  </div>
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
        <tr>
          <td>{row.id}</td>
          <td>{row.name}</td>
          <td>{row.site || '—'}</td>
          <td>{row.notes || '—'}</td>
          <td>
            {#if row.archived}
              <span class="badge archived">已归档</span>
            {:else}
              <span class="badge active">使用中</span>
            {/if}
          </td>
          <td class="ops">
            <button class="link-btn" on:click={() => edit(row)}>编辑</button>
            {#if row.archived}
              <button class="link-btn" on:click={() => unarchive(row)}>解档</button>
            {:else}
              <button class="link-btn danger" on:click={() => archive(row)}>归档</button>
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
  .list-head {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 0.6rem;
  }

  .toggle {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.85rem;
    color: var(--steel);
    cursor: pointer;
  }

  .notice {
    border: 1px solid rgba(46, 160, 67, 0.5);
    background: rgba(46, 160, 67, 0.12);
    color: #7ee2a0;
    padding: 0.6rem 0.9rem;
    border-radius: 3px;
    margin-bottom: 1rem;
  }

  .badge.archived {
    color: var(--steel);
    border: 1px solid var(--line);
    padding: 0.1rem 0.5rem;
    border-radius: 2px;
    font-size: 0.78rem;
  }

  .badge.active {
    color: #7ee2a0;
    border: 1px solid rgba(46, 160, 67, 0.5);
    padding: 0.1rem 0.5rem;
    border-radius: 2px;
    font-size: 0.78rem;
  }
</style>
