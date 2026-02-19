import type { ReactNode } from "react";

interface Props {
  header: ReactNode;
  sidebar: ReactNode;
  tabBar: ReactNode;
  children: ReactNode;
  bottomBar?: ReactNode;
}

export function AppShell({ header, sidebar, tabBar, children, bottomBar }: Props) {
  return (
    <div className="h-full flex flex-col">
      {header}
      <div className="flex flex-1 min-h-0">
        {sidebar}
        <div className="flex flex-col flex-1 min-w-0">
          {tabBar}
          <main className="flex-1 min-h-0 relative">
            {children}
          </main>
          {bottomBar && (
            <div className="border-t border-border bg-panel shrink-0">
              {bottomBar}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
