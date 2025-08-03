import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const { pathname, searchParams } = request.nextUrl;

  const normalizePath = (path: string) =>
    path !== '/' && path.endsWith('/') ? path.slice(0, -1) : path;

  const normalizedPathname = normalizePath(pathname);

  // Define public routes that don't require authentication.
  // To expose a new public route, add its base path (e.g. '/about') to this array.
  const publicRoutes = ['/login'];

  const normalizedPublicRoutes = publicRoutes.map(normalizePath);
  const isPublicRoute = normalizedPublicRoutes.includes(normalizedPathname);

  const isAuthenticated = request.cookies.get('soleil_auth') ||
                         searchParams.get('auth') === 'success';

  if (isPublicRoute) {
    if (normalizedPathname === '/login' && isAuthenticated) {
      const hasProfile = request.cookies.get('soleil_profile_complete');
      if (hasProfile) {
        return NextResponse.redirect(new URL('/dashboard', request.url));
      } else {
        return NextResponse.redirect(new URL('/profile', request.url));
      }
    }
    return NextResponse.next();
  }

  // If trying to access a protected route without authentication, redirect to login
  if (!isAuthenticated) {
    const loginUrl = new URL('/login/', request.url);
    // Only set redirect parameter for meaningful paths
    if (normalizedPathname !== '/') {
      loginUrl.searchParams.set('redirect', normalizedPathname);
    }
    return NextResponse.redirect(loginUrl);
  }
  
  // If authenticated and accessing root, redirect based on profile status
  if (isAuthenticated && normalizedPathname === '/') {
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
    '/((?!_next/static|_next/image|favicon.ico|icons|manifest.json|sw\.js|workbox-.*\.js).*)',
  ],
};
