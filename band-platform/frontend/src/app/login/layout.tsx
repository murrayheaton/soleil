export default function LoginLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Don't wrap login page in the main Layout component
  // This prevents any event interference from the navigation layout
  return <>{children}</>;
}