import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const { pathname, searchParams } = request.nextUrl;
  
  // Define public routes that don't require authentication
  const publicRoutes = ['/login'];
  
  // If accessing login page, always allow it through (no redirects)
  if (pathname === '/login') {
    // If already authenticated, redirect away from login
    const isAuthenticated = request.cookies.get('soleil_auth') || 
                           searchParams.get('auth') === 'success';
    
    if (isAuthenticated) {
      const hasProfile = request.cookies.get('soleil_profile_complete');
      if (hasProfile) {
        return NextResponse.redirect(new URL('/dashboard', request.url));
      } else {
        return NextResponse.redirect(new URL('/profile', request.url));
      }
    }
    
    // Not authenticated - allow access to login page
    return NextResponse.next();
  }
  
  // For all other routes, check authentication
  const isAuthenticated = request.cookies.get('soleil_auth') || 
                         searchParams.get('auth') === 'success';
  
  // If trying to access a protected route without authentication, redirect to login
  const isPublicRoute = publicRoutes.includes(pathname);
  if (!isPublicRoute && !isAuthenticated) {
    const loginUrl = new URL('/login', request.url);
    // Only set redirect parameter for meaningful paths
    if (pathname !== '/') {
      loginUrl.searchParams.set('redirect', pathname);
    }
    return NextResponse.redirect(loginUrl);
  }
  
  // If authenticated and accessing root, redirect based on profile status
  if (isAuthenticated && pathname === '/') {
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