import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const { pathname, searchParams } = request.nextUrl;
  
  // Define public routes that don't require authentication
  const publicRoutes = ['/login'];
  
  // Check if the current route is public
  const isPublicRoute = publicRoutes.some(route => pathname === route);
  
  // Check for authentication - for now we'll use a simple cookie check
  // In production, this should verify a JWT or session token
  const isAuthenticated = request.cookies.get('soleil_auth') || 
                         searchParams.get('auth') === 'success';
  
  // If trying to access a protected route without authentication, redirect to login
  if (!isPublicRoute && !isAuthenticated) {
    const loginUrl = new URL('/login', request.url);
    if (pathname !== '/') {
      loginUrl.searchParams.set('redirect', pathname);
    }
    return NextResponse.redirect(loginUrl);
  }
  
  // If authenticated and trying to access root or login, redirect based on profile status
  if (isAuthenticated && (pathname === '/' || pathname === '/login')) {
    // Check if user has completed profile setup
    const hasProfile = request.cookies.get('soleil_profile_complete');
    
    if (hasProfile) {
      return NextResponse.redirect(new URL('/dashboard', request.url));
    } else {
      return NextResponse.redirect(new URL('/profile', request.url));
    }
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
     */
    '/((?!_next/static|_next/image|favicon.ico|icons|manifest.json).*)',
  ],
};