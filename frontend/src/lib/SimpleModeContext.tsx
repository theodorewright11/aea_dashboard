"use client";

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";

interface SimpleModeContextValue {
  isSimple: boolean;
  toggle: () => void;
}

const SimpleModeContext = createContext<SimpleModeContextValue>({
  isSimple: false,
  toggle: () => {},
});

const STORAGE_KEY = "aea_simple_mode";

export function SimpleModeProvider({ children }: { children: ReactNode }) {
  const [isSimple, setIsSimple] = useState(false);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored === "true") setIsSimple(true);
    } catch {
      // localStorage unavailable
    }
    setHydrated(true);
  }, []);

  const toggle = useCallback(() => {
    setIsSimple((prev) => {
      const next = !prev;
      try { localStorage.setItem(STORAGE_KEY, String(next)); } catch { /* noop */ }
      return next;
    });
  }, []);

  // Avoid hydration mismatch: render children immediately but context value
  // reflects stored preference only after mount
  const value: SimpleModeContextValue = {
    isSimple: hydrated ? isSimple : false,
    toggle,
  };

  return (
    <SimpleModeContext.Provider value={value}>
      {children}
    </SimpleModeContext.Provider>
  );
}

export function useSimpleMode(): SimpleModeContextValue {
  return useContext(SimpleModeContext);
}
