import { DemoNav } from "@/components/DemoNav";

export default function DemoLayout({ children }: LayoutProps<"/demo">) {
  return (
    <>
      <DemoNav />
      <main className="flex-1">{children}</main>
    </>
  );
}
