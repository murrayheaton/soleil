import SoleilLogo from '@/components/SoleilLogo';

export default function LoginLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Login page gets its own minimal layout without navigation
  return (
    <div className="min-h-screen" style={{backgroundColor: '#171717'}}>
      {/* Header with just the logo */}
      <header style={{
        padding: '1.5rem 2rem',
        borderBottom: '1px solid #262626'
      }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
          <SoleilLogo size="medium" />
        </div>
      </header>
      
      {/* Main content */}
      <main>
        {children}
      </main>
    </div>
  );
}