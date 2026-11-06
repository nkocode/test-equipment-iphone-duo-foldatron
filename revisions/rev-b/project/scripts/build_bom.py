"""Render the procurement table from hardware/BOM.json."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    data = json.loads((ROOT / "hardware/BOM.json").read_text())
    rows = data["items"]
    totals = {}
    for row in rows:
        row["extended_estimate_usd"] = round(
            row["quantity"] * row["unit_estimate_usd"], 2
        )
        group = row["category"]
        totals[group] = totals.get(group, 0) + row["extended_estimate_usd"]
    station = sum(
        value
        for group, value in totals.items()
        if group not in {"Tools", "Optional"}
    )
    data.update(
        station_total=station,
        category_totals=totals,
        tools_total=totals["Tools"],
        optional_total=totals["Optional"],
    )
    (ROOT / "hardware/BOM.json").write_text(json.dumps(data, indent=2) + "\n")
    lines = [
        "# Bill of materials - one FoldBench station",
        "",
        f"USD planning allowances, {data['date']}. Verify quotes, interfaces "
        "and availability before ordering. Phone, taxes, shipping, "
        "machine-shop labor and workshop machinery are excluded. "
        "Fastener quantities include spares.",
        "",
        f"**Station parts: ${station:,.2f}.** Tools if not owned: "
        f"${totals['Tools']:,.2f}. Optional observation/charging: "
        f"${totals['Optional']:,.2f}. Add a 25% station-parts contingency "
        f"(${station * 0.25:,.2f}) for a planning total of "
        f"${station * 1.25:,.2f} before tools, optional items and labor.",
        "",
    ]
    for group, total in totals.items():
        lines.extend(
            [
                f"## {group} - ${total:,.2f}",
                "",
                "| ID | Qty | Item / specification | Unit USD | Ext. USD "
                "| Source |",
                "| --- | ---: | --- | ---: | ---: | --- |",
            ]
        )
        for row in rows:
            if row["category"] != group:
                continue
            source = row["source_or_procurement"]
            if source.startswith("https"):
                source = f"[Vendor/reference]({source})"
            lines.append(
                f"| {row['id']} | {row['quantity']} | {row['item']}: "
                f"{row['specification']} | {row['unit_estimate_usd']:.2f} | "
                f"{row['extended_estimate_usd']:.2f} | {source} |"
            )
        lines.append("")
    (ROOT / "hardware/BOM.md").write_text("\n".join(lines))
    print(f"{len(rows)} BOM items; station parts ${station:,.2f}")


if __name__ == "__main__":
    main()
