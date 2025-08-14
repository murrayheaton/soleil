# Fix Google Drive Chart Integration

## 🎯 **Objective**
Connect the existing Google Drive services to the API endpoints so bands can actually see and download their charts from murray@projectbrass.live.

## 📋 **Requirements**
1. **Backend API Implementation**: Connect Google Drive services to chart endpoints
2. **Chart Listing**: Implement `/charts` endpoint to list charts from Google Drive
3. **Chart Download**: Implement `/charts/{chart_id}/download` endpoint for file streaming
4. **Frontend Integration**: Fix frontend API service to properly call these endpoints
5. **Google Drive Authentication**: Ensure proper OAuth flow for murray@projectbrass.live account
6. **Error Handling**: Robust error handling for Google Drive API failures
7. **Testing**: Verify charts can be listed and downloaded

## 🔍 **Current State Analysis**
- ✅ Google Drive services exist and are well-implemented
- ✅ Frontend ChartViewer component exists and expects working API
- ❌ All chart API endpoints return "Not Implemented" (501 errors)
- ❌ No connection between Google Drive services and API routes
- ❌ Frontend can't display charts due to broken API calls

## 🏗️ **Implementation Architecture**
1. **Backend Layer**: Connect `GoogleDriveService` to content API routes
2. **API Layer**: Implement chart listing, metadata, and download endpoints
3. **Service Layer**: Create chart service that uses Google Drive integration
4. **Frontend Layer**: Fix API service calls and error handling
5. **Integration Layer**: Test full flow from Google Drive to chart display

## 📁 **Files to Modify**
- `band-platform/backend/modules/content/api/content_routes.py` - Implement chart endpoints
- `band-platform/backend/modules/content/services/` - Create chart service
- `band-platform/frontend/src/lib/api.ts` - Fix API service (if exists)
- `band-platform/frontend/src/components/ChartViewer.tsx` - Ensure proper API calls

## 🎯 **Success Criteria**
- [ ] Charts can be listed from Google Drive account
- [ ] Chart files can be downloaded and displayed
- [ ] Frontend shows charts instead of errors
- [ ] Proper error handling for Google Drive issues
- [ ] Authentication flow works for murray@projectbrass.live

## 🚀 **Priority: HIGH**
This is blocking core functionality - bands need to see their charts to perform live.

## 🔧 **Technical Approach**
1. **Phase 1**: Implement backend chart service using existing Google Drive integration
2. **Phase 2**: Connect service to API endpoints
3. **Phase 3**: Test with murray@projectbrass.live account
4. **Phase 4**: Fix frontend integration
5. **Phase 5**: End-to-end testing

## 💡 **Expected Outcome**
Bands will finally be able to see and use their charts from Google Drive, making the platform actually functional for live performances.
