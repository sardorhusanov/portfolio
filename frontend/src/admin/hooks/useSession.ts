import { useEffect, useSyncExternalStore } from "react";
import { ensureSession, sessionStore } from "../../api/adminClient";
export function useSession() {
  const session = useSyncExternalStore(
    sessionStore.subscribe,
    sessionStore.getSnapshot,
  );
  useEffect(() => {
    void ensureSession();
  }, []);
  return session;
}
