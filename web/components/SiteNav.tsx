"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function SiteNav() {
  const pathname = usePathname() ?? "/";
  const isZh = pathname === "/zh" || pathname.startsWith("/zh/");

  if (isZh) {
    return (
      <nav className="text-sm text-[color:var(--color-muted)] flex items-center gap-5">
        <Link href="/zh" className="hover:text-white">今日</Link>
        <Link href="/zh/archive" className="hover:text-white">歷史</Link>
        <Link href="/zh/learn" className="hover:text-white">入門</Link>
        <span className="text-white/20">·</span>
        <Link href="/" className="hover:text-white">EN</Link>
        <Link href="/zh" className="hover:text-white">中</Link>
      </nav>
    );
  }

  return (
    <nav className="text-sm text-[color:var(--color-muted)] flex items-center gap-5">
      <Link href="/" className="hover:text-white">Today</Link>
      <Link href="/archive" className="hover:text-white">Archive</Link>
      <Link href="/learn" className="hover:text-white">Learn</Link>
      <span className="text-white/20">·</span>
      <Link href="/" className="hover:text-white">EN</Link>
      <Link href="/zh" className="hover:text-white">中</Link>
    </nav>
  );
}
