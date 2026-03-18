from __future__ import annotations

import argparse
import csv
import math
import random
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path


@dataclass(frozen=True)
class ProjectProfile:
	project_id: str
	project_type: str
	commission_date: date
	initial_investment: float
	base_daily_revenue: float
	fixed_daily_cost: float
	variable_cost_ratio: float
	utilization_mean: float
	utilization_spread: float


def daterange(start: date, end: date):
	current = start
	while current <= end:
		yield current
		current += timedelta(days=1)


def clip(value: float, lower: float, upper: float) -> float:
	return max(lower, min(value, upper))


def build_project_profiles(
	start_date: date,
	projects_per_type: int,
	rng: random.Random,
) -> list[ProjectProfile]:
	type_configs = {
		"solar": {
			"investment": (2_000_000, 8_000_000),
			"revenue": (11_000, 28_000),
			"fixed_cost": (1_900, 4_000),
			"var_ratio": (0.18, 0.28),
			"util": (0.23, 0.10),
		},
		"wind": {
			"investment": (5_000_000, 16_000_000),
			"revenue": (22_000, 54_000),
			"fixed_cost": (3_500, 8_000),
			"var_ratio": (0.20, 0.32),
			"util": (0.37, 0.10),
		},
		"hydro": {
			"investment": (10_000_000, 30_000_000),
			"revenue": (35_000, 95_000),
			"fixed_cost": (7_000, 16_000),
			"var_ratio": (0.15, 0.25),
			"util": (0.52, 0.08),
		},
	}

	profiles: list[ProjectProfile] = []
	for project_type, cfg in type_configs.items():
		for index in range(1, projects_per_type + 1):
			commission_offset = rng.randint(0, 365 * 2)
			commission_date = start_date + timedelta(days=commission_offset)
			profiles.append(
				ProjectProfile(
					project_id=f"{project_type[:2].upper()}-{index:03d}",
					project_type=project_type,
					commission_date=commission_date,
					initial_investment=rng.uniform(*cfg["investment"]),
					base_daily_revenue=rng.uniform(*cfg["revenue"]),
					fixed_daily_cost=rng.uniform(*cfg["fixed_cost"]),
					variable_cost_ratio=rng.uniform(*cfg["var_ratio"]),
					utilization_mean=cfg["util"][0],
					utilization_spread=cfg["util"][1],
				)
			)

	return profiles


def market_regime(day_index: int, current_date: date, rng: random.Random) -> dict[str, float | str]:
	trend = 0.00012 * day_index
	seasonal = 0.03 * math.sin(2 * math.pi * current_date.timetuple().tm_yday / 365.25)
	energy_price_index = 100.0 * (1 + trend + seasonal + rng.gauss(0.0, 0.008))

	policy_support = clip(0.60 + 0.00003 * day_index + rng.gauss(0.0, 0.05), 0.10, 0.95)
	carbon_credit_index = 72.0 * (1 + 0.0002 * day_index + rng.gauss(0.0, 0.03))

	incentive_event = "none"
	policy_event_chance = rng.random()
	if policy_event_chance < 0.003:
		incentive_event = "tax_credit_extension"
		policy_support = clip(policy_support + 0.10, 0.10, 1.00)
	elif policy_event_chance < 0.006:
		incentive_event = "tariff_adjustment"
		policy_support = clip(policy_support - 0.08, 0.00, 1.00)

	return {
		"energy_price_index": round(energy_price_index, 2),
		"policy_support": round(policy_support, 3),
		"carbon_credit_index": round(carbon_credit_index, 2),
		"incentive_event": incentive_event,
	}


def generate_rows(
	start_date: date,
	end_date: date,
	projects_per_type: int,
	seed: int,
) -> list[dict[str, str | float]]:
	rng = random.Random(seed)
	profiles = build_project_profiles(start_date, projects_per_type, rng)
	rows: list[dict[str, str | float]] = []

	for day_index, day in enumerate(daterange(start_date, end_date)):
		indicators = market_regime(day_index, day, rng)

		for project in profiles:
			if day < project.commission_date:
				continue

			project_age_days = (day - project.commission_date).days
			maturity_bonus = 1.0 + 0.00004 * min(project_age_days, 2200)

			seasonal_util = 0.04 * math.sin(
				2 * math.pi * (day.timetuple().tm_yday + project_age_days % 30) / 365.25
			)
			raw_utilization = (
				project.utilization_mean
				+ seasonal_util
				+ rng.gauss(0.0, project.utilization_spread / 3)
			)
			capacity_utilization = clip(raw_utilization, 0.08, 0.95)

			sentiment_base = 0.50 * float(indicators["policy_support"]) + 0.002 * (
				float(indicators["energy_price_index"]) - 100
			)
			sentiment_score = clip(sentiment_base + rng.gauss(0.0, 0.23) - 0.10, -1.0, 1.0)

			revenue = (
				project.base_daily_revenue
				* maturity_bonus
				* capacity_utilization
				* (float(indicators["energy_price_index"]) / 100)
				* (1 + 0.06 * sentiment_score)
			)

			operating_costs = (
				project.fixed_daily_cost
				* (1 + 0.00008 * day_index)
				+ revenue * project.variable_cost_ratio
				+ rng.uniform(-180, 180)
			)
			operating_costs = max(400.0, operating_costs)

			initial_investment = 0.0
			if day == project.commission_date:
				initial_investment = project.initial_investment
			elif rng.random() < 0.0015:
				initial_investment = rng.uniform(12_000, 120_000)

			net_profit = revenue - operating_costs - initial_investment

			rows.append(
				{
					"Date": day.isoformat(),
					"Project ID": project.project_id,
					"Project Type": project.project_type,
					"Initial Investment": round(initial_investment, 2),
					"Revenue": round(revenue, 2),
					"Operating Costs": round(operating_costs, 2),
					"Net Profit": round(net_profit, 2),
					"Capacity Utilization": round(capacity_utilization * 100, 2),
					"Market Indicators": (
						f"energy_price_index={indicators['energy_price_index']};"
						f"policy_support={indicators['policy_support']};"
						f"carbon_credit_index={indicators['carbon_credit_index']};"
						f"event={indicators['incentive_event']}"
					),
					"Sentiment Score": round(sentiment_score, 3),
				}
			)

	return rows


def write_csv(rows: list[dict[str, str | float]], output_path: Path) -> None:
	output_path.parent.mkdir(parents=True, exist_ok=True)
	fieldnames = [
		"Date",
		"Project ID",
		"Project Type",
		"Initial Investment",
		"Revenue",
		"Operating Costs",
		"Net Profit",
		"Capacity Utilization",
		"Market Indicators",
		"Sentiment Score",
	]

	with output_path.open("w", newline="", encoding="utf-8") as csv_file:
		writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
		writer.writeheader()
		writer.writerows(rows)


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description=(
			"Generate a realistic daily time-series renewable energy financial dataset "
			"for financial advising and predictive modeling."
		)
	)
	parser.add_argument(
		"--start-date",
		type=date.fromisoformat,
		default=date(2018, 1, 1),
		help="Dataset start date in YYYY-MM-DD format.",
	)
	parser.add_argument(
		"--end-date",
		type=date.fromisoformat,
		default=date(2025, 12, 31),
		help="Dataset end date in YYYY-MM-DD format.",
	)
	parser.add_argument(
		"--projects-per-type",
		type=int,
		default=6,
		help="Number of projects to simulate per project type.",
	)
	parser.add_argument(
		"--seed",
		type=int,
		default=42,
		help="Random seed for reproducible output.",
	)
	parser.add_argument(
		"--output",
		type=Path,
		default=Path(__file__).with_name("renewable_energy_financial_timeseries.csv"),
		help="Path to output CSV file.",
	)

	args = parser.parse_args()
	if args.start_date > args.end_date:
		parser.error("--start-date must be earlier than or equal to --end-date")
	if args.projects_per_type <= 0:
		parser.error("--projects-per-type must be greater than 0")

	return args


def main() -> None:
	args = parse_args()
	rows = generate_rows(
		start_date=args.start_date,
		end_date=args.end_date,
		projects_per_type=args.projects_per_type,
		seed=args.seed,
	)
	write_csv(rows, args.output)
	print(f"Generated {len(rows):,} rows at {args.output}")


if __name__ == "__main__":
	main()
