import { useEffect } from 'react';
import { backendBaseUrl } from '../apiBase';

export function useGalaxySseRefresh({ onRelevantEvent }) {
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) return undefined;

    let es;
    try {
      es = new EventSource(`${backendBaseUrl}/api/events/stream?token=${encodeURIComponent(token)}`);
    } catch (e) {
      return undefined;
    }

    const onActivity = (evt) => {
      try {
        const payload = JSON.parse(evt.data || '{}');
        const type = (payload?.event_type || '').toLowerCase();
        const relevant =
          type.includes('fleet') ||
          type.includes('planet') ||
          type.includes('colon') ||
          type.includes('combat') ||
          type.includes('pirate') ||
          type.includes('explor') ||
          type.includes('rename') ||
          type.includes('debris') ||
          type.includes('recycle');
        if (!relevant) return;
        onRelevantEvent?.(payload);
      } catch (e) {
        // ignore
      }
    };

    es.addEventListener('activity', onActivity);
    es.addEventListener('error', () => {
      try {
        es.close();
      } catch (e) {
        // ignore
      }
    });

    return () => {
      try {
        es.close();
      } catch (e) {
        // ignore
      }
    };
  }, [onRelevantEvent]);
}
