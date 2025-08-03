import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const { pathname, searchParams } = request.nextUrl;
  
  // Define public routes that don't require authentication
  const publicRoutes = ['/', '/login', '/api/auth'];
  
  // Check if the current route is public
  const isPublicRoute = publicRoutes.some(route => 
    pathname === route || pathname.startsWith(`${route}/`)
  );
  
  // Check for authentication session cookie
  const sessionCookie = request.cookies.get('soleil_session');
  
  // Allow access if coming from successful auth callback
  const authSuccess = searchParams.get('auth') === 'success';
  
  // If accessing a protected route without authentication, redirect to login
  if (!isPublicRoute && !sessionCookie && !authSuccess) {
    const loginUrl = new URL('/login', request.url);
    // Add the original URL as a redirect parameter
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }
  
  // If authenticated user tries to access login page or root, redirect to dashboard
  if ((sessionCookie || authSuccess) && (pathname === '/login' || pathname === '/')) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }
  
  // Allow the request to continue
  return NextResponse.next();
}

// Configure which routes the middleware should run on
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public files (public directory)
     * - api routes that handle their own auth
     */
    '/((?!_next/static|_next/image|favicon.ico|icons|manifest.json|api/auth).*)',
  ],
};