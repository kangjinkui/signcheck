import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AdJudge — 광고판정 시스템',
  description: '강남구 옥외광고물 판정 보조 시스템',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>
        <header>
          <div className="container">
            <h1>AdJudge 광고판정 시스템</h1>
            <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
              <span>강남구 내부 시스템</span>
              <a href="/admin">관리자</a>
            </div>
          </div>
        </header>
        {children}
      </body>
    </html>
  );
}
