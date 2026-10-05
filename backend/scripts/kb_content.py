KB_ARTICLES = [
    # ---------------- billing ----------------
    {"title": "Why was I charged twice?", "category": "billing", "content": (
        "A duplicate charge is usually a pending authorization that appears next to the final "
        "charge. Authorizations are released by your bank within 3 to 5 business days and no money "
        "is taken. If both charges show as settled after 5 business days, contact support with the "
        "last four digits of your card and the transaction dates, and we will refund the duplicate "
        "within 7 business days.")},
    {"title": "How to request a refund", "category": "billing", "content": (
        "Annual plans are refundable within 14 days of purchase and monthly plans within 48 hours "
        "of renewal. Open Settings, then Billing, then Request refund, or reply to your invoice "
        "email. Approved refunds return to the original payment method in 5 to 10 business days. "
        "Cancelling a plan stops future renewals but does not automatically refund the current "
        "billing period.")},
    {"title": "Updating payment methods and downloading invoices", "category": "billing", "content": (
        "Go to Settings, Billing, Payment methods to add or replace a card. If a card is declined, "
        "check that international and online payments are enabled with your bank. Invoices, "
        "including GST invoices, are available under Billing, Invoices. Add your tax ID in Billing "
        "details before the renewal date so it appears on the next invoice.")},
    # ---------------- account ----------------
    {"title": "Resetting your password", "category": "account", "content": (
        "Select Forgot password on the login page and enter your account email. The reset email "
        "arrives within 5 minutes; check spam and promotions folders and make sure "
        "noreply@nimbus.example is not blocked. Reset links expire after 30 minutes. If you still "
        "receive nothing, confirm you are using the email the account was created with, or ask "
        "support to verify your identity.")},
    {"title": "Two-factor authentication setup and recovery", "category": "account", "content": (
        "Two-factor codes are time based, so make sure your phone clock is set to automatic time. "
        "If codes are rejected, resync your authenticator app. If you lost your device, use one of "
        "the ten backup codes saved at setup. Without backup codes, support can reset two-factor "
        "after identity verification, which takes up to 24 hours.")},
    {"title": "Locked accounts, suspicious logins and account deletion", "category": "account",
     "content": (
        "Accounts lock for 30 minutes after five failed login attempts. If you see a login from an "
        "unknown location, change your password immediately and sign out of all sessions under "
        "Settings, Security. To delete your account go to Settings, Privacy, Delete account. "
        "Deletion removes personal data within 30 days and cannot be undone.")},
    # ---------------- technical ----------------
    {"title": "Troubleshooting crashes and freezes", "category": "technical", "content": (
        "Update to the latest version of the app first, since most crashes are fixed in patch "
        "releases. Clear the app cache under Settings, Advanced, restart the device, and reinstall "
        "if the problem persists. When reporting a crash, include the app version, device model, "
        "operating system version, and the steps that trigger it so engineers can reproduce it.")},
    {"title": "Slow performance and sync problems", "category": "technical", "content": (
        "Slow loading is often caused by very large workspaces or unstable connections. Check "
        "status.nimbus.example for incidents, switch networks, and disable browser extensions that "
        "block scripts. For files that do not sync, sign out and in again to force a full resync "
        "and confirm you have free storage on your plan. Sync usually recovers within 15 minutes "
        "after reconnecting.")},
    {"title": "Export and upload errors", "category": "technical", "content": (
        "Uploads are limited to 100 MB per file on Pro plans and 25 MB on Free plans. Error 500 "
        "during upload or export usually means a temporary server issue, so wait a few minutes and "
        "retry. Exports of more than 50,000 rows are generated in the background and emailed as a "
        "download link. If the error persists, send the request time and your workspace ID to "
        "support.")},
    # ---------------- shipping ----------------
    {"title": "Tracking your order", "category": "shipping", "content": (
        "Orders ship within 2 business days and tracking is emailed once the carrier scans the "
        "package. Standard delivery takes 4 to 7 business days and express takes 2 to 3. Tracking "
        "may show no updates for up to 48 hours after dispatch. If tracking has not moved for 5 "
        "business days, contact support with your order number and we will open a carrier "
        "investigation.")},
    {"title": "Missing, delayed or damaged packages", "category": "shipping", "content": (
        "If a package is marked delivered but missing, check with neighbors and building "
        "reception, then wait 24 hours as carriers sometimes scan early. After that, contact us "
        "with your order number and we will file a carrier claim and ship a replacement or issue "
        "a refund. For damaged or wrong items, send photos of the item and packaging within 14 "
        "days of delivery.")},
    {"title": "Returns, exchanges and address changes", "category": "shipping", "content": (
        "Unused items can be returned within 30 days. Generate a prepaid return label under "
        "Orders, Return item. Refunds are issued within 5 business days after the warehouse "
        "receives the return. Delivery addresses can be changed only before the order ships, from "
        "Orders, Edit address. After dispatch, contact the carrier to redirect the parcel.")},
    # ---------------- integrations ----------------
    {"title": "Webhooks: delivery, retries and 5xx errors", "category": "integrations", "content": (
        "Webhooks are sent as signed POST requests and expect a 2xx response within 10 seconds. "
        "Failed deliveries are retried up to 8 times with exponential backoff over 24 hours. A "
        "502 or 504 response usually means your endpoint or its proxy is timing out or "
        "unreachable, so check your server logs, firewall and TLS certificate. Review delivery "
        "attempts and replay events under Developers, Webhooks.")},
    {"title": "API keys, authentication and rate limits", "category": "integrations", "content": (
        "Create API keys under Developers, API keys and send them as a Bearer token. A 401 error "
        "means the key is missing, revoked, or belongs to a different workspace. A 429 error means "
        "you exceeded the limit of 100 requests per minute on Pro or 1,000 on Business; honor the "
        "Retry-After header and use exponential backoff. Rotate keys every 90 days.")},
    {"title": "Connecting Slack, Zapier, Salesforce and Google Calendar", "category": "integrations",
     "content": (
        "Integrations use OAuth, so reconnecting usually fixes disconnects: remove the "
        "integration under Settings, Integrations and add it again, approving all requested "
        "permissions. OAuth redirect errors are often caused by blocked third-party cookies or a "
        "stale browser session, so retry in a private window. Salesforce duplicates can be "
        "prevented by choosing email as the matching key in the sync settings.")},
    # ---------------- general ----------------
    {"title": "Plans, pricing and discounts", "category": "general", "content": (
        "Nimbus offers Free, Pro, Business and Enterprise plans. Pro is billed per seat monthly or "
        "annually with a discount for annual billing. Verified students and non-profits receive "
        "50 percent off Pro. Enterprise pricing depends on seat count and requirements such as "
        "SSO, audit logs and a dedicated success manager; contact sales for a quote.")},
    {"title": "Demos, security documents and data processing agreements", "category": "general",
     "content": (
        "Book a product demo from the Contact sales page and a specialist will reply within one "
        "business day. Our security overview, SOC 2 report summary and standard data processing "
        "agreement are available in the Trust Center. Custom agreements for Enterprise customers "
        "are handled by the legal team and typically take 5 to 10 business days.")},
    {"title": "Feature requests and feedback", "category": "general", "content": (
        "Submit ideas through the Feedback board in the app so others can vote on them. The "
        "product team reviews the top requests every month and publishes decisions in the public "
        "roadmap. Dark mode is available under Settings, Appearance. We cannot promise delivery "
        "dates for individual requests, but every submission is read.")},
]