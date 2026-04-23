import client from './client';

export interface VdabSyncResult {
  import?: {
    upserted?: number;
    fetched?: number;
    fallback?: boolean;
  };
  enrichment?: unknown;
}

export async function runVdabSync(aantal = 100): Promise<VdabSyncResult> {
  const { data } = await client.post(`/sync?aantal=${encodeURIComponent(aantal)}`);
  return data;
}
