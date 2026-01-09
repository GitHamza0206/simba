"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { useSession, useActiveOrganization, useListOrganizations, organization } from "@/lib/auth-client";
import { setActiveOrgId, clearActiveOrgId } from "@/lib/api";

interface AuthContextType {
  session: ReturnType<typeof useSession>["data"];
  isLoading: boolean;
  isReady: boolean;
  activeOrganization: ReturnType<typeof useActiveOrganization>["data"];
  organizations: ReturnType<typeof useListOrganizations>["data"];
  setActiveOrganization: (orgId: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const { data: session, isPending: isSessionLoading } = useSession();
  const { data: activeOrg, isPending: isOrgLoading } = useActiveOrganization();
  const { data: organizations, isPending: isOrgsLoading } = useListOrganizations();
  const [isSettingOrg, setIsSettingOrg] = useState(false);

  // Sync active org to localStorage for API client
  useEffect(() => {
    if (activeOrg?.id) {
      setActiveOrgId(activeOrg.id);
    } else {
      clearActiveOrgId();
    }
  }, [activeOrg?.id]);

  // Auto-set active organization if user has orgs but none is active
  useEffect(() => {
    if (session && organizations && organizations.length > 0 && !activeOrg && !isSettingOrg) {
      setIsSettingOrg(true);
      organization.setActive({ organizationId: organizations[0].id }).finally(() => {
        setIsSettingOrg(false);
      });
    }
  }, [session, organizations, activeOrg, isSettingOrg]);

  const setActiveOrganization = async (orgId: string) => {
    await organization.setActive({ organizationId: orgId });
  };

  const isLoading = isSessionLoading || isOrgLoading || isOrgsLoading || isSettingOrg;
  // Ready when we have a session and an active org (or no orgs at all)
  const isReady = !isLoading && !!session && (!!activeOrg || (organizations?.length === 0));

  return (
    <AuthContext.Provider
      value={{
        session,
        isLoading,
        isReady,
        activeOrganization: activeOrg,
        organizations,
        setActiveOrganization,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
