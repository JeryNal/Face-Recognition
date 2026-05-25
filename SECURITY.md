# Security Policy

## Reporting Security Vulnerabilities

**Please do not open public issues for security vulnerabilities.**

If you discover a security vulnerability, please email security@example.com instead of using the issue tracker. We will investigate and patch security issues promptly.

### When Reporting

Please include:
1. Description of the vulnerability
2. Steps to reproduce
3. Affected versions
4. Potential impact
5. Any suggested remediation

### What to Expect

- Initial acknowledgment within 48 hours
- Status update within 7 days
- Security patch release within 30 days (critical issues within 7 days)
- Public disclosure coordinated with you

## Security Features

### Authentication
- Session-based authentication with Flask-Login
- CSRF protection on all forms
- Secure password hashing
- Account verification workflow

### Data Protection
- Audit logging of all security events
- IP address tracking for suspicious activity
- Email notifications for security events
- Secure session token management

### Infrastructure
- HTTPS recommended for production
- SQL injection prevention through ORM
- XSS protection via Jinja2 templating
- CORS headers configured

## Dependency Security

We regularly update dependencies to patch security vulnerabilities. Run:
```bash
pip install --upgrade -r requirements.txt
pip list --outdated
```

To check for known vulnerabilities:
```bash
pip install safety
safety check
```

## Best Practices for Users

1. **Keep Software Updated**: Always use the latest version
2. **Use HTTPS**: Deploy with SSL/TLS certificates
3. **Strong Passwords**: Enforce password complexity
4. **Regular Audits**: Review audit logs regularly
5. **Environment Variables**: Never commit secrets to git
6. **2FA**: Enable multi-factor authentication where available

## Known Vulnerabilities

See [GitHub Security Tab](https://github.com/JeryNal/Face-Recognition/security) for known vulnerabilities and patches.

## Version Support

| Version | Status | Support Until |
|---------|--------|----------------|
| 1.0.x | Current | Active |
| 0.x | Deprecated | 2024-12-31 |

Security patches are provided for current and previous versions. Older versions are not supported.

## Contact

For security inquiries:
- Email: security@example.com
- GitHub Issues: For non-security issues only

## Security Advisories

We publish security advisories on GitHub. Subscribe to receive notifications:
1. Go to repository
2. Watch → Custom → Releases
3. Select "Dependabot alerts"

---

**Last Updated**: May 25, 2026
