# Email Domain Change: botsmith.ai → botsmith.io

**Date:** December 13, 2025  
**Change Type:** Domain Migration  
**Status:** ✅ COMPLETE

---

## Summary

Successfully changed all email domain references from `@botsmith.ai` to `@botsmith.io` across the entire application.

---

## Files Updated (14 files)

### Documentation Files
1. `INVESTOR_PITCH_DOCUMENT.md` - founders@botsmith.io
2. `WHITE_LABEL_FEATURE_COMPLETE.md` - Reference links
3. `WHITE_LABEL_BUG_FIX.md` - Reference links

### Frontend Components
4. `frontend/src/components/Footer.jsx` - support@botsmith.io

### Frontend Pages
5. `frontend/src/pages/PrivacyPolicy.jsx` 
   - privacy@botsmith.io
   - dpo@botsmith.io

6. `frontend/src/pages/CookiePolicy.jsx`
   - privacy@botsmith.io
   - support@botsmith.io

7. `frontend/src/pages/TermsOfService.jsx` - legal@botsmith.io

8. `frontend/src/pages/ForgotPassword.jsx` - support@botsmith.io (mailto link)

9. `frontend/src/pages/PublicChat.jsx` - botsmith.io link

10. `frontend/src/pages/resources/Documentation.jsx` - support@botsmith.io (mailto link)

11. `frontend/src/pages/resources/HelpCenter.jsx` - support@botsmith.io

12. `frontend/src/pages/resources/ApiDocs.jsx` - api.botsmith.io references

13. `frontend/src/pages/resources/articles/Installation.jsx` - botsmith.io

### Widget Files
14. `frontend/public/fast-widget.js` - botsmith.io links (2 occurrences)

---

## Email Addresses Changed

| Email Type | Old Address | New Address |
|------------|-------------|-------------|
| Support | support@botsmith.ai | **support@botsmith.io** |
| Privacy | privacy@botsmith.ai | **privacy@botsmith.io** |
| Data Protection Officer | dpo@botsmith.ai | **dpo@botsmith.io** |
| Legal | legal@botsmith.ai | **legal@botsmith.io** |
| Founders | founders@botsmith.ai | **founders@botsmith.io** |

---

## Changes by Component

### Footer Component
- Contact email updated to `support@botsmith.io`

### Privacy Policy
- Privacy contact: `privacy@botsmith.io`
- Data Protection Officer: `dpo@botsmith.io`

### Cookie Policy
- Privacy contact: `privacy@botsmith.io`
- Support contact: `support@botsmith.io`

### Terms of Service
- Legal contact: `legal@botsmith.io`

### Help Center
- Support contact: `support@botsmith.io`
- Mailto links updated

### Documentation
- Support contact mailto links updated to `support@botsmith.io`

### Forgot Password Page
- Support contact link: `support@botsmith.io`

### API Documentation
- All API endpoint examples updated to `api.botsmith.io`

### Widget (fast-widget.js)
- Powered by links updated to `https://botsmith.io`

### Public Chat
- Footer link updated to `https://botsmith.io`

---

## Technical Changes

### Search & Replace Operation
```bash
find . -type f \( -name "*.js" -o -name "*.jsx" -o -name "*.py" -o -name "*.md" \) \
  ! -path "*/node_modules/*" ! -path "*/.git/*" \
  -exec sed -i 's/botsmith\.ai/botsmith.io/g' {} \;
```

### Files Scanned
- JavaScript files (*.js)
- React components (*.jsx)
- Python files (*.py)
- Markdown documentation (*.md)

### Exclusions
- node_modules directory
- .git directory

---

## Service Restart

Frontend service restarted to apply changes:
```bash
sudo supervisorctl restart frontend
```

**Status:** Frontend compiled successfully with updated email references

---

## Verification

✅ All 14 files updated successfully  
✅ 5 email addresses changed (support, privacy, dpo, legal, founders)  
✅ Widget links updated  
✅ API documentation updated  
✅ Frontend service restarted  
✅ No errors during compilation  

---

## Testing Checklist

- [x] Footer displays support@botsmith.io
- [x] Privacy Policy shows privacy@botsmith.io and dpo@botsmith.io
- [x] Cookie Policy shows privacy@botsmith.io and support@botsmith.io
- [x] Terms of Service shows legal@botsmith.io
- [x] Help Center contact is support@botsmith.io
- [x] Forgot Password support link points to support@botsmith.io
- [x] Widget "Powered by" links to botsmith.io
- [x] Public chat footer links to botsmith.io
- [x] API docs reference api.botsmith.io
- [x] Documentation support links work correctly

---

## Impact

**User-Facing Changes:**
- All contact email addresses now use @botsmith.io domain
- All website links point to botsmith.io
- Widget footer links updated
- API documentation examples updated

**Developer Impact:**
- None - all changes are content/reference updates
- No code logic changes
- No API changes
- No database changes

**SEO/Branding:**
- Brand consistency with .io domain
- Professional appearance
- Aligned with tech industry standards

---

## Rollback Plan

If needed, changes can be reversed with:
```bash
find . -type f \( -name "*.js" -o -name "*.jsx" -o -name "*.py" -o -name "*.md" \) \
  ! -path "*/node_modules/*" ! -path "*/.git/*" \
  -exec sed -i 's/botsmith\.io/botsmith.ai/g' {} \;
sudo supervisorctl restart frontend
```

---

## Notes

- No database changes required (admin email remains admin@botsmith.com)
- Backend services did not require restart (no backend code changes)
- Hot reload will pick up most changes automatically
- Widget updates will be reflected in embedded chatbots on next load

---

**Completed By:** Main Agent  
**Completion Time:** ~2 minutes  
**Status:** ✅ SUCCESSFUL
