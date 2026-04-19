"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { cn } from "@/lib/utils";

const nav = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/analyze", label: "Analyze" },
  { href: "/history", label: "History" },
  { href: "/analytics", label: "Analytics" },
  { href: "/profile", label: "Profile" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-64 flex-shrink-0 border-r border-slate-800 bg-slate-900/50 md:flex md:flex-col">
        <div className="border-b border-slate-800 px-5 py-6">
          <Link href="/dashboard" className="text-lg font-semibold tracking-tight text-white">
            Sentiment<span className="text-sky-400">SaaS</span>
          </Link>
          <p className="mt-1 text-xs text-slate-500">Insights from text, face & voice</p>
        </div>
        <nav className="flex flex-1 flex-col gap-1 p-3">
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                pathname === item.href
                  ? "bg-sky-600/20 text-sky-300"
                  : "text-slate-400 hover:bg-slate-800 hover:text-white",
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="border-t border-slate-800 p-4 text-xs text-slate-500">
          Signed in as
          <div className="truncate font-medium text-slate-300">{user?.email}</div>
          <button
            type="button"
            onClick={() => logout()}
            className="mt-3 w-full rounded-lg border border-slate-700 py-2 text-slate-300 hover:bg-slate-800"
          >
            Log out
          </button>
        </div>
      </aside>

      <div className="flex min-h-screen flex-1 flex-col">
        <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur md:hidden">
          <div className="flex items-center justify-between px-4 py-3">
            <Link href="/dashboard" className="font-semibold text-white">
              SentimentSaaS
            </Link>
            <button type="button" onClick={() => logout()} className="text-sm text-sky-400">
              Log out
            </button>
          </div>
          <nav className="flex gap-1 overflow-x-auto px-2 pb-2 text-sm">
            {nav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "whitespace-nowrap rounded-full px-3 py-1",
                  pathname === item.href
                    ? "bg-sky-600/30 text-sky-200"
                    : "text-slate-400 hover:bg-slate-800",
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </header>
        <header className="hidden border-b border-slate-800 bg-slate-950/60 px-8 py-5 md:block">
          <h1 className="text-xl font-semibold text-white">
            {nav.find((n) => n.href === pathname)?.label ?? "App"}
          </h1>
        </header>
        <main className="flex-1 px-4 py-6 md:px-8">{children}</main>
      </div>
    </div>
  );
}
