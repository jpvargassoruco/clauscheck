import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types/domain";

export type Theme = "light" | "dark" | "system";

interface AuthState {
  accessToken: string | null;
  user: User | null;
  currentOrgId: string | null;
  theme: Theme;
  setSession: (accessToken: string, user: User) => void;
  setAccessToken: (accessToken: string | null) => void;
  setUser: (user: User | null) => void;
  setCurrentOrg: (orgId: string) => void;
  setTheme: (theme: Theme) => void;
  logout: () => void;
}

/**
 * El access token vive SOLO en memoria (no persist) por seguridad;
 * el refresh token lo maneja el backend (cookie httpOnly) o se
 * reenvía en el body de /auth/refresh según arranque de sesión.
 * currentOrgId y theme sí persisten (preferencias de UI, no secretos).
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      user: null,
      currentOrgId: null,
      theme: "system",
      setSession: (accessToken, user) =>
        set({
          accessToken,
          user,
          currentOrgId: user.orgs[0]?.org.id ?? null
        }),
      setAccessToken: (accessToken) => set({ accessToken }),
      setUser: (user) => set({ user }),
      setCurrentOrg: (orgId) => set({ currentOrgId: orgId }),
      setTheme: (theme) => set({ theme }),
      logout: () => set({ accessToken: null, user: null, currentOrgId: null })
    }),
    {
      name: "clauscheck-auth",
      partialize: (state) => ({
        currentOrgId: state.currentOrgId,
        theme: state.theme
      })
    }
  )
);
