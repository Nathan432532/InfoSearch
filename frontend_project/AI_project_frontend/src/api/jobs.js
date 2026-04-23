import client from './client';

export async function runVdabSync(aantal = 100) {
  const { data } = await client.post(`/sync?aantal=${encodeURIComponent(aantal)}`);
  return data;
}

export default {
  runVdabSync,
};
