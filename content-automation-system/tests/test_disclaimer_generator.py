import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.website_builder import generate_disclaimer_page


def test_recipe_disclaimer_renders_affiliate_and_niche_sections():
    html = generate_disclaimer_page(
        {
            "siteName": "Example Kitchen",
            "domain": "example-kitchen.test",
            "contactEmail": "hello@example-kitchen.test",
            "effectiveDate": "May 13, 2026",
            "companyName": "Example Kitchen LLC",
            "country": "United States",
            "businessType": "recipe website",
            "nicheType": "recipes",
            "usesAffiliateLinks": True,
            "affiliatePrograms": ["Amazon Associates", "ShareASale"],
            "usesAds": True,
            "linksToThirdPartySites": True,
            "allowsUserGeneratedContent": True,
            "publishesProductReviews": True,
            "sellsProducts": True,
        }
    )

    assert "<!doctype html>" in html
    assert "<main class=\"disclaimer-wrap\">" in html
    assert "Example Kitchen" in html
    assert "example-kitchen.test" in html
    assert "hello@example-kitchen.test" in html
    assert "May 13, 2026" in html
    assert "General Information Disclaimer" in html
    assert "Accuracy and No Warranty" in html
    assert "Limitation of Liability" in html
    assert "External Links Disclaimer" in html
    assert "Affiliate Disclosure" in html
    assert "As an Amazon Associate, we earn from qualifying purchases" in html
    assert "ShareASale" in html
    assert "Advertising Disclaimer" in html
    assert "User-Generated Content Disclaimer" in html
    assert "Product Reviews and Opinions" in html
    assert "Products, Purchases, and E-Commerce" in html
    assert "Recipe, Nutrition, Allergy, and Dietary Disclaimer" in html
    assert "{{" not in html
    assert "[[" not in html


def test_finance_disclaimer_renders_financial_risk_and_omits_recipe_section():
    html = generate_disclaimer_page(
        {
            "siteName": "Money Notes",
            "domain": "money.example",
            "contactEmail": "contact@money.example",
            "nicheType": "finance",
            "usesAffiliateLinks": False,
            "usesAds": False,
            "linksToThirdPartySites": False,
        }
    )

    assert "Financial and Investment Disclaimer" in html
    assert "Markets, investments, income opportunities, and business outcomes involve risk" in html
    assert "Recipe, Nutrition, Allergy, and Dietary Disclaimer" not in html
    assert "Affiliate Disclosure" not in html
    assert "Advertising Disclaimer" not in html
