import { useEffect, useState } from 'react';

/**
 * Minimal hash router: routes look like "#/plants/3/analyze".
 * Kept dependency-free on purpose (no router library needed for V1).
 */
export interface Route {
  path: string;            // e.g. "/plants/3/analyze"
  segments: string[];      // ["plants", "3", "analyze"]
}

function parse(): Route {
  const hash = window.location.hash.replace(/^#/, '') || '/';
  return { path: hash, segments: hash.split('/').filter(Boolean) };
}

export function useRoute(): Route {
  const [route, setRoute] = useState<Route>(parse);
  useEffect(() => {
    const onChange = () => setRoute(parse());
    window.addEventListener('hashchange', onChange);
    return () => window.removeEventListener('hashchange', onChange);
  }, []);
  return route;
}

export function navigate(to: string): void {
  window.location.hash = to;
}
