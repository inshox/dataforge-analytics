import { create } from "zustand";
import { persist } from "zustand/middleware";

export type WorkspaceTab = {
  id: string;
  label: string;
  href: string;
};

type TabState = {
  tabs: WorkspaceTab[];
  activeId: string | null;
  openTab: (tab: WorkspaceTab) => void;
  closeTab: (id: string) => void;
  setActive: (id: string) => void;
};

export const useTabStore = create<TabState>()(
  persist(
    (set) => ({
      tabs: [{ id: "home", label: "Home", href: "/dashboard" }],
      activeId: "home",
      openTab: (tab) =>
        set((s) => {
          const exists = s.tabs.find((t) => t.id === tab.id);
          return {
            tabs: exists ? s.tabs : [...s.tabs, tab].slice(-12),
            activeId: tab.id,
          };
        }),
      closeTab: (id) =>
        set((s) => {
          const tabs = s.tabs.filter((t) => t.id !== id);
          const activeId = s.activeId === id ? tabs[tabs.length - 1]?.id ?? null : s.activeId;
          return { tabs: tabs.length ? tabs : [{ id: "home", label: "Home", href: "/dashboard" }], activeId };
        }),
      setActive: (id) => set({ activeId: id }),
    }),
    { name: "dataforge-tabs" }
  )
);
