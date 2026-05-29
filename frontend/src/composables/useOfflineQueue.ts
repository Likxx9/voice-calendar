/* ============================================================
 * M6 组合式函数 — 离线操作队列缓存
 * IndexedDB 离线队列 | 版本戳管理 | 同步上传
 * ============================================================ */

import { ref, computed } from 'vue'
import type { OfflineOperation, SyncPayload, SyncState } from '@/types/contracts'

const DB_NAME = 'vc_offline_db'
const STORE_NAME = 'offline_operations'
const DB_VERSION = 1

export function useOfflineQueue() {
  const queue = ref<OfflineOperation[]>([])
  const syncState = ref<SyncState>('online')
  const pendingCount = computed(() => queue.value.length)
  const isOnline = ref(navigator.onLine)

  // ── IndexedDB 操作 ──────────────────────────────
  function openDB(): Promise<IDBDatabase> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION)

      request.onupgradeneeded = () => {
        const db = request.result
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          db.createObjectStore(STORE_NAME, { keyPath: 'operation_id' })
        }
      }

      request.onsuccess = () => resolve(request.result)
      request.onerror = () => reject(request.error)
    })
  }

  // 从 IndexedDB 加载所有离线操作
  async function loadQueue() {
    try {
      const db = await openDB()
      const tx = db.transaction(STORE_NAME, 'readonly')
      const store = tx.objectStore(STORE_NAME)

      return new Promise<void>((resolve, reject) => {
        const request = store.getAll()
        request.onsuccess = () => {
          queue.value = request.result || []
          resolve()
        }
        request.onerror = () => reject(request.error)
      })
    } catch (err) {
      console.error('[OfflineQueue] 加载失败:', err)
    }
  }

  // 添加离线操作到队列
  async function enqueue(operation: Omit<OfflineOperation, 'operation_id' | 'executed_at'>) {
    const op: OfflineOperation = {
      ...operation,
      operation_id: `op_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      executed_at: new Date().toISOString(),
    }

    try {
      const db = await openDB()
      const tx = db.transaction(STORE_NAME, 'readwrite')
      tx.objectStore(STORE_NAME).add(op)
      queue.value.push(op)
    } catch (err) {
      console.error('[OfflineQueue] 入队失败:', err)
    }
  }

  // 移除已同步成功的操作
  async function dequeue(operationId: string) {
    try {
      const db = await openDB()
      const tx = db.transaction(STORE_NAME, 'readwrite')
      tx.objectStore(STORE_NAME).delete(operationId)
      queue.value = queue.value.filter(op => op.operation_id !== operationId)
    } catch (err) {
      console.error('[OfflineQueue] 出队失败:', err)
    }
  }

  // 清空已同步的操作
  async function clearSynced(operationIds: string[]) {
    try {
      const db = await openDB()
      const tx = db.transaction(STORE_NAME, 'readwrite')
      const store = tx.objectStore(STORE_NAME)
      for (const id of operationIds) {
        store.delete(id)
      }
      queue.value = queue.value.filter(op => !operationIds.includes(op.operation_id))
    } catch (err) {
      console.error('[OfflineQueue] 批量清除失败:', err)
    }
  }

  // 构建同步载荷
  function buildSyncPayload(userId: string): SyncPayload {
    return {
      user_id: userId,
      client_timestamp: new Date().toISOString(),
      offline_operations: [...queue.value],
    }
  }

  // ── 网络状态监听 ────────────────────────────────
  function initNetworkListener() {
    window.addEventListener('online', () => {
      isOnline.value = true
      syncState.value = queue.value.length > 0 ? 'syncing' : 'online'
    })

    window.addEventListener('offline', () => {
      isOnline.value = false
      syncState.value = 'offline'
    })
  }

  // 生成版本标签
  function generateVersionTag(): string {
    return `v_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`
  }

  // 初始化
  loadQueue()
  initNetworkListener()

  return {
    queue,
    syncState,
    pendingCount,
    isOnline,
    enqueue,
    dequeue,
    clearSynced,
    buildSyncPayload,
    generateVersionTag,
    loadQueue,
  }
}
