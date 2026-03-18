from __future__ import annotations

import argparse
import csv
from pathlib import Path


def build_faq_dataset() -> list[dict[str, str]]:
	"""Return FAQ rows for organic/non-GMO coffee shop offerings."""
	faq_rows = [
		{
			"question": "What does organic coffee mean at your coffee shop?",
			"answer": "Our organic coffee is grown without synthetic pesticides, herbicides, or fertilizers and is sourced from farms that meet certified organic standards.",
		},
		{
			"question": "How can organic coffee support overall wellness?",
			"answer": "Organic coffee reduces exposure to certain synthetic chemical residues, which many guests prefer as part of a cleaner daily routine.",
		},
		{
			"question": "Are your non-GMO drinks actually free from genetically modified ingredients?",
			"answer": "Yes, our non-GMO drinks use ingredients sourced from suppliers that verify their products are not genetically modified.",
		},
		{
			"question": "Why do some customers choose non-GMO milk alternatives?",
			"answer": "Some customers choose non-GMO oat, almond, or soy alternatives because they prefer ingredients developed without genetic engineering.",
		},
		{
			"question": "Do organic teas provide the same flavor as conventional teas?",
			"answer": "Yes, and many guests describe our organic teas as clean, aromatic, and full-bodied because of careful cultivation and handling.",
		},
		{
			"question": "What health-focused options do you offer besides coffee?",
			"answer": "We offer organic teas, non-GMO smoothies, and low-sugar seasonal drinks made with whole-food ingredients when possible.",
		},
		{
			"question": "How do you source your organic coffee beans?",
			"answer": "We partner with importers and roasters that trace beans back to certified organic farms and prioritize transparent supply chains.",
		},
		{
			"question": "Do you work with farms that use sustainable practices?",
			"answer": "Yes, we prioritize farms using soil-building methods, water stewardship, biodiversity protection, and responsible labor practices.",
		},
		{
			"question": "How do you verify non-GMO ingredients in syrups and flavorings?",
			"answer": "We request supplier documentation and ingredient disclosures to confirm non-GMO status for key components in our menu.",
		},
		{
			"question": "Are your pastries made with organic ingredients?",
			"answer": "Several pastries are made with organic flour, organic eggs, and non-GMO oils, and we label these options in-store.",
		},
		{
			"question": "What makes your organic cold brew unique?",
			"answer": "Our organic cold brew uses slow extraction, small-batch roasting, and single-origin beans for a smooth, naturally sweet profile.",
		},
		{
			"question": "Do you have non-GMO breakfast items?",
			"answer": "Yes, we carry non-GMO granola cups, chia puddings, and breakfast sandwiches made with verified non-GMO ingredients.",
		},
		{
			"question": "Can organic coffee be part of a balanced lifestyle?",
			"answer": "Yes, when consumed in moderation, organic coffee can fit well into a balanced routine that includes hydration and nutrient-dense foods.",
		},
		{
			"question": "Do you offer drinks without artificial colors or preservatives?",
			"answer": "Yes, many of our organic and non-GMO drinks avoid artificial colors, artificial sweeteners, and unnecessary preservatives.",
		},
		{
			"question": "How do your sourcing practices support coffee-growing communities?",
			"answer": "We work with partners focused on fair pricing, long-term buying relationships, and community investment in producing regions.",
		},
		{
			"question": "Are your decaf options also organic?",
			"answer": "Yes, we offer organic decaf options processed with methods designed to preserve flavor while removing most caffeine.",
		},
		{
			"question": "What non-GMO sweetener options do you have?",
			"answer": "We provide non-GMO cane sugar, organic honey, and select naturally derived syrup options with simple ingredient lists.",
		},
		{
			"question": "How is your organic matcha sourced?",
			"answer": "Our organic matcha comes from certified farms that follow traditional shade-growing and careful leaf processing practices.",
		},
		{
			"question": "Do organic ingredients change the nutritional quality of your menu?",
			"answer": "Nutritional values still depend on the full recipe, but organic ingredients can align with customer preferences for cleaner sourcing.",
		},
		{
			"question": "Which menu items highlight both organic and non-GMO standards?",
			"answer": "Our signature lattes, select smoothies, and house granola parfaits are built around ingredients that meet both organic and non-GMO criteria.",
		},
		{
			"question": "What makes your seasonal organic drinks different from typical café specials?",
			"answer": "We use whole spices, real fruit purées, and minimally processed ingredients instead of high-fructose or artificially flavored bases.",
		},
		{
			"question": "Can I find low-caffeine organic options at your shop?",
			"answer": "Yes, we offer organic herbal teas, half-caf blends, and naturally low-caffeine drink choices throughout the day.",
		},
		{
			"question": "How do you reduce additives in your non-GMO beverage lineup?",
			"answer": "We prioritize short ingredient labels, avoid unnecessary stabilizers when possible, and select suppliers with clean-formulation standards.",
		},
		{
			"question": "Do you disclose ingredient origins to customers?",
			"answer": "Yes, we share origin and sourcing details for many core ingredients through menu notes and staff training.",
		},
		{
			"question": "Is your chocolate used in mochas non-GMO?",
			"answer": "Yes, our mocha base uses non-GMO cocoa ingredients and avoids artificial flavor additives.",
		},
		{
			"question": "What are the benefits of choosing organic herbal tea?",
			"answer": "Organic herbal tea can be a soothing, caffeine-free option made without synthetic agricultural chemicals.",
		},
		{
			"question": "How do you ensure quality from farm to cup?",
			"answer": "We use lot tracking, roast-date controls, and supplier audits to maintain freshness, consistency, and sourcing transparency.",
		},
		{
			"question": "Do you carry non-GMO protein add-ins for smoothies?",
			"answer": "Yes, we offer non-GMO protein options including pea and whey selections verified by our ingredient review process.",
		},
		{
			"question": "Why are your organic beans sometimes priced higher?",
			"answer": "Organic certification, lower-input farming methods, and traceable sourcing can increase production costs compared with conventional beans.",
		},
		{
			"question": "Can non-GMO choices still taste indulgent?",
			"answer": "Absolutely, our non-GMO menu includes rich mochas, creamy frappes, and dessert-inspired lattes made with carefully selected ingredients.",
		},
		{
			"question": "Do you offer kid-friendly organic or non-GMO drinks?",
			"answer": "Yes, we have kid-friendly steamers and fruit-forward drinks using organic or non-GMO ingredients with reduced added sugar options.",
		},
		{
			"question": "How do you choose suppliers for organic snacks?",
			"answer": "We evaluate certifications, ingredient quality, allergen controls, and supply reliability before adding organic snacks to our shelves.",
		},
		{
			"question": "Are your bottled beverages aligned with your sourcing standards?",
			"answer": "Yes, we stock bottled drinks that match our focus on organic, non-GMO, and clean-label ingredient sourcing.",
		},
		{
			"question": "Do you have organic options for customers avoiding dairy?",
			"answer": "Yes, we offer organic plant-based milk options and dairy-free recipes across multiple hot and iced drinks.",
		},
		{
			"question": "What is unique about your single-origin organic coffees?",
			"answer": "They highlight distinct regional flavor notes while maintaining organic farming standards and transparent origin traceability.",
		},
		{
			"question": "How do your non-GMO offerings support ingredient transparency?",
			"answer": "Our non-GMO standards require clear supplier documentation and straightforward ingredient statements that customers can understand.",
		},
		{
			"question": "Do organic and non-GMO mean the same thing on your menu?",
			"answer": "No, organic focuses on farming methods and prohibited inputs, while non-GMO indicates ingredients are not genetically engineered.",
		},
		{
			"question": "Can I customize drinks to keep them cleaner and lighter?",
			"answer": "Yes, you can request unsweetened bases, non-GMO add-ins, and lower-sugar preparations for many beverages.",
		},
		{
			"question": "How often do you review sourcing standards?",
			"answer": "We review supplier certifications and ingredient disclosures regularly to maintain alignment with organic and non-GMO commitments.",
		},
		{
			"question": "Do you offer wellness-focused add-ons for coffee and tea?",
			"answer": "Yes, we provide options like cinnamon, turmeric blends, and functional ingredients selected for quality and compatibility with our sourcing values.",
		},
	]
	return faq_rows


def write_csv(rows: list[dict[str, str]], output_file: Path) -> None:
	output_file.parent.mkdir(parents=True, exist_ok=True)

	with output_file.open("w", newline="", encoding="utf-8") as csv_file:
		writer = csv.DictWriter(csv_file, fieldnames=["question", "answer"])
		writer.writeheader()
		writer.writerows(rows)


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description=(
			"Generate a FAQ dataset with two columns (question, answer) for "
			"organic and non-GMO coffee shop foods and drinks."
		)
	)
	parser.add_argument(
		"--output",
		type=Path,
		default=Path(__file__).with_name("coffee_shop_faq_dataset.csv"),
		help="Output CSV file path.",
	)
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	rows = build_faq_dataset()
	write_csv(rows, args.output)
	print(f"Generated {len(rows)} FAQ rows at: {args.output}")


if __name__ == "__main__":
	main()
