import { RequireAuth } from "@/components/app-shell";

export default function OnboardingLayout({ children }: { children: React.ReactNode }) {
  return <RequireAuth>{children}</RequireAuth>;
}
