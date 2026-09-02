import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types/domain";

export type Theme = "light" | "dark" | "system";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  currentOrgId: string | null;
  theme: Theme;
  setSession: (tokens: { accessToken: string; refreshToken: string }, user: User) => void;
  setTokens: (tokens: { accessToken: string; refreshToken: string }) => void;
  setUser: (user: User | null) => void;
  setCurrentOrg: (orgId: string) => void;
  setTheme: (theme: Theme) => void;
  logout: () => void;
}

/**
 * La API real (`POST /auth/refresh`) no usa cookie httpOnly: exige
 * `refresh_token` en el body de cada llamado. Por eso, a diferencia del
 * access token (solo en memoria), el refresh token SÍ persiste (es lo único
 * que permite renovar la sesión tras recargar la página). currentOrgId y
 * theme también persisten (preferencias de UI).
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      currentOrgId: null,
      theme: "system",
      setSession: ({ accessToken, refreshToken }, user) =>
        set({
          accessToken,
          refreshToken,
          user,
          currentOrgId: user.orgs[0]?.id ?? null
        }),
      setTokens: ({ accessToken, refreshToken }) => set({ accessToken, refreshToken }),
      setUser: (user) => set({ user }),
      setCurrentOrg: (orgId) => set({ currentOrgId: orgId }),
      setTheme: (theme) => set({ theme }),
      logout: () => set({ accessToken: null, refreshToken: null, user: null, currentOrgId: null })
    }),
    {
      name: "clauscheck-auth",
      partialize: (state) => ({
        refreshToken: state.refreshToken,
        currentOrgId: state.currentOrgId,
        theme: state.theme
      })
    }
  )
);
