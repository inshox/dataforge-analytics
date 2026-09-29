export default function DatasetViewLayout({ children }: { children: React.ReactNode }) {
  return children;
}

/** Static HTML shell for Tauri export */
export function generateStaticParams() {
  return [{}];
}
