/**
 * Root layout — wraps every page with the sidebar navigation shell.
 *
 * ALL STYLE IMPORTS happen here from the styles/ folder.
 * Individual pages don't import CSS — they just use the class names
 * defined in the corresponding styles/ file.
 */

import '@/styles/globals.css';
import '@/styles/layout.css';
import '@/styles/dashboard.css';
import '@/styles/stocks.css';
import '@/styles/tags.css';
import Link from 'next/link';

export const metadata = {
  title: 'Sectoral API — Stock Screener Dashboard',
  description: 'Track Indian equity stocks, AI-generated sector tags, and weekly returns.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <div className="app-shell">
          {/* ── Sidebar ─────────────────────────────────────── */}
          <aside className="sidebar">
            <div className="sidebar-brand">
              <h1>Sectoral</h1>
              <p>Stock Intelligence</p>
            </div>

            <nav className="nav-section">
              <div className="nav-label">Overview</div>
              <Link href="/" className="nav-link">
                <span className="nav-icon">📊</span>
                Dashboard
              </Link>

              <div className="nav-label">Market Data</div>
              <Link href="/stocks" className="nav-link">
                <span className="nav-icon">📈</span>
                Stocks
              </Link>
              <Link href="/tags" className="nav-link">
                <span className="nav-icon">🏷️</span>
                Tags & Returns
              </Link>
            </nav>
          </aside>

          {/* ── Main Content ────────────────────────────────── */}
          <main className="main-content">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
