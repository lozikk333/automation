import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.website_builder import generate_privacy_policy_page


def test_gdpr_privacy_policy_renders_dynamic_sections():
    html = generate_privacy_policy_page(
        {
            "siteName": "Example Journal",
            "domain": "example.com",
            "contactEmail": "hello@example.com",
            "effectiveDate": "May 13, 2026",
            "companyName": "Example Media Ltd",
            "country": "Germany",
            "businessType": "informational content website",
            "collectsNames": True,
            "collectsEmails": True,
            "collectsIPAddresses": True,
            "usesCookies": True,
            "usesAnalytics": True,
            "usesNewsletter": True,
            "usesContactForms": True,
            "allowsComments": True,
            "hasUserAccounts": True,
            "usesAds": True,
            "usesAffiliateLinks": True,
            "dataControllerName": "Example Media Ltd",
            "dataControllerEmail": "privacy@example.com",
            "hasDPO": True,
            "dpoEmail": "dpo@example.com",
            "legalBasisConsent": True,
            "legalBasisLegitimateInterest": True,
            "legalBasisContract": True,
            "legalBasisLegalObligation": True,
            "storesDataInEU": False,
            "usesThirdPartyProcessors": True,
        }
    )

    assert "<!doctype html>" in html
    assert "<main class=\"policy-wrap\">" in html
    assert "Example Journal" in html
    assert "example.com" in html
    assert "May 13, 2026" in html
    assert "Example Media Ltd" in html
    assert "privacy@example.com" in html
    assert "dpo@example.com" in html
    assert "Right of access" in html
    assert "Right to rectification" in html
    assert "Right to erasure" in html
    assert "Right to restrict processing" in html
    assert "Right to object" in html
    assert "Right to data portability" in html
    assert "Right to withdraw consent" in html
    assert "Right to lodge a complaint" in html
    assert "International Data Transfers" in html
    assert "Third-Party Processors" in html
    assert "Cookies and Similar Technologies" in html
    assert "Contractual necessity" in html
    assert "{{" not in html
    assert "[[" not in html


def test_gdpr_privacy_policy_omits_disabled_optional_sections():
    html = generate_privacy_policy_page(
        {
            "siteName": "Quiet Notes",
            "domain": "quiet.example",
            "contactEmail": "privacy@quiet.example",
            "usesCookies": False,
            "usesAnalytics": False,
            "usesNewsletter": False,
            "usesAds": False,
            "usesAffiliateLinks": False,
            "usesThirdPartyProcessors": False,
            "storesDataInEU": True,
        }
    )

    assert "Cookies and Similar Technologies" not in html
    assert "Third-Party Processors" not in html
    assert "International Data Transfers" not in html
    assert "display, measure, and improve advertising" not in html
    assert "track affiliate referrals" not in html
