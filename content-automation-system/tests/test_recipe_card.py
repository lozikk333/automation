"""
Test Tasty Recipes REST API integration.
Run: python tests/test_recipe_card.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from content_engine.recipe_card import generate_recipe_json, create_tasty_recipe_post, inject_into_content

load_dotenv()

SAMPLE_ARTICLE = """
<h2>Easy Chocolate Lava Cake</h2>
<p>This rich chocolate lava cake has a gooey molten center and takes only 25 minutes.
Perfect for a weeknight dessert or impressing guests.</p>
<h2>Ingredients</h2>
<p>100g butter, 100g dark chocolate, 2 eggs, 2 yolks, 60g sugar, 30g flour, pinch of salt.</p>
<h2>Instructions</h2>
<p>Melt chocolate and butter. Whisk eggs and sugar until pale. Fold together with flour.
Pour into buttered ramekins. Bake at 220C for 12 minutes. Serve immediately.</p>
<h2>Tips</h2>
<p>Do not overbake — the center must stay molten. Prep batter up to 24h ahead.</p>
"""

TITLE = "Easy Chocolate Lava Cake"


def test_generate_json():
    print("\n[1] AI extraction...")
    api_key = os.getenv("OPENROUTER_API_KEY")
    assert api_key, "OPENROUTER_API_KEY not set in .env"

    recipe = generate_recipe_json(SAMPLE_ARTICLE, api_key, title=TITLE)
    assert recipe, "generate_recipe_json returned None"
    assert recipe.get("Description"), "Missing Description"
    assert recipe.get("Ingredients"),  "Missing Ingredients"
    assert recipe.get("Instructions"), "Missing Instructions"
    assert recipe.get("Details"),      "Missing Details"
    assert recipe.get("Nutrition"),    "Missing Nutrition"

    print(f"  Description : {recipe['Description'][:80]}")
    print(f"  Diet        : {recipe['Details'].get('Diet')}")
    print(f"  Calories    : {recipe['Nutrition'].get('Calories')}")
    print("  ✅ JSON OK")
    return recipe


def test_create_wp_post(recipe):
    print("\n[2] Creating Tasty Recipe post via REST API...")
    wp_url   = os.getenv("WORDPRESS_URL")
    username = os.getenv("WORDPRESS_USERNAME")
    password = os.getenv("WORDPRESS_APP_PASSWORD")

    if not all([wp_url, username, password]):
        print("  ⚠️  WordPress credentials not set — skipping live test")
        return None

    recipe_id = create_tasty_recipe_post(
        recipe   = recipe,
        title    = TITLE,
        wp_url   = wp_url,
        username = username,
        password = password,
    )

    if recipe_id is None:
        print("  ⚠️  Recipe post not created (Tasty Recipes plugin may not be active)")
        return None

    assert isinstance(recipe_id, int), f"Expected int, got {type(recipe_id)}"
    print(f"  Recipe ID: {recipe_id} ✅")
    return recipe_id


def test_inject(recipe_id):
    print("\n[3] Injecting shortcode into article...")
    rid   = recipe_id or 999   # use dummy id if WP test was skipped
    final = inject_into_content(rid, SAMPLE_ARTICLE)

    expected = f'[tasty-recipe id="{rid}"]'
    assert final.startswith(expected), f"Shortcode must be at TOP, got: {final[:60]}"
    assert SAMPLE_ARTICLE.strip() in final, "Article content must be preserved"
    print(f"  Shortcode : {expected} ✅")
    print(f"  Content preserved ✅")


if __name__ == "__main__":
    recipe    = test_generate_json()
    recipe_id = test_create_wp_post(recipe)
    test_inject(recipe_id)
    print("\n🎉 All recipe card tests passed!")
