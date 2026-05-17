import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from content_engine.article_generator import ArticleGenerator

load_dotenv()


async def test():
    api_key = os.getenv("OPENROUTER_API_KEY")
    assert api_key, "OPENROUTER_API_KEY not set in .env"

    gen = ArticleGenerator(api_key)
    result = await gen.generate_complete_article("chocolate lava cake")

    # SEO checks
    print(f"\n--- SEO ---")
    print(f"Title:       {result['title']} ({len(result['title'])} chars)")
    print(f"Meta desc:   {result['meta_description']} ({len(result['meta_description'])} chars)")
    print(f"Slug:        {result['slug']}")
    assert len(result["title"]) <= 60, f"Title too long: {len(result['title'])} chars"
    assert 140 <= len(result["meta_description"]) <= 165, f"Meta desc length off: {len(result['meta_description'])}"
    assert result["slug"], "Slug is empty"
    print("✅ SEO metadata OK")

    # Sections check
    print(f"\n--- Sections ---")
    print(f"Sections generated: {len(result['sections'])}")
    assert len(result["sections"]) >= 5, "Expected at least 5 sections"
    for s in result["sections"]:
        assert s["content"].strip(), f"Empty content in section: {s['title']}"
        print(f"  [{s['level']}] {s['title']} — {len(s['content'].split())} words")
    print("✅ Sections OK")

    # HTML check
    print(f"\n--- HTML ---")
    assert "<h2>" in result["html_content"], "Missing h2 tags in HTML"
    assert "<p>" in result["html_content"], "Missing p tags in HTML"
    print(f"HTML length: {len(result['html_content'])} chars")
    print("✅ HTML output OK")

    # Recipe card check
    print(f"\n--- Recipe Card ---")
    recipe = result["recipe_card"]
    print(f"Prep: {recipe.get('prep_time')} min, Cook: {recipe.get('cook_time')} min, Serves: {recipe.get('servings')}")
    assert recipe.get("ingredients"), "Recipe has no ingredients"
    assert recipe.get("instructions"), "Recipe has no instructions"
    print(f"Ingredients: {len(recipe['ingredients'])}, Steps: {len(recipe['instructions'])}")
    print("✅ Recipe card OK")

    print("\n🎉 All content generation checks passed!")
    return result


if __name__ == "__main__":
    asyncio.run(test())
