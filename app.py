from flask import Flask, render_template, request, jsonify
import pandas as pd
from sqlalchemy import create_engine
import db_config  # import database credentials

app = Flask(__name__)

# Create SQLAlchemy engine using db_config
engine = create_engine(db_config.SQLALCHEMY_DATABASE_URI)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/autocomplete")
def autocomplete():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])

    sql = """
        SELECT
            entry AS uniprot,
            gene_names,
            protein_names
        FROM uniprot_entries
        WHERE entry LIKE %(q)s
           OR gene_names LIKE %(q)s
           OR protein_names LIKE %(q)s
        LIMIT 20
    """

    df = pd.read_sql(sql, engine, params={"q": f"%{query}%"})

    suggestions = []
    for _, row in df.iterrows():
        # Prefer gene name → protein name → UniProt accession
        label = (
            row["protein_names"]
            or row["gene_names"]
            or row["uniprot"]
        )
        suggestions.append(label)

    # Remove duplicates while preserving order
    suggestions = list(dict.fromkeys(suggestions))

    return jsonify(suggestions)


@app.route("/results", methods=["POST"])
def results():
    query = request.form.get("query", "").strip()
    show_silent = request.form.get("show_silent", "off") == "on"

    # Fetch variants
    sql_variants = """
        SELECT
            u.uniprot_id,
            u.entry AS uniprot,
            u.gene_names,
            u.length,
            v.variant_id,
            v.mutation_aa,
            v.aa_mut_start,
            v.mutation_desc_aa
        FROM uniprot_entries u
        LEFT JOIN variants v
            ON u.uniprot_id = v.uniprot_id
        WHERE u.gene_names LIKE %(q)s
           OR u.entry LIKE %(q)s
        ORDER BY u.entry, v.aa_mut_start
        LIMIT 1000
    """
    df = pd.read_sql(sql_variants, engine, params={"q": f"%{query}%"})

    # Fetch PPI data for all matching proteins
    proteins = df["uniprot"].dropna().unique().tolist()
    if proteins:
        sql_ppi = """
            SELECT proteinA_uniprot, proteinB_uniprot, experimental_system, experimental_system_type, pubmed_id
            FROM interactions
            WHERE proteinA_uniprot IN %(proteins)s
               OR proteinB_uniprot IN %(proteins)s
        """
        df_ppi = pd.read_sql(sql_ppi, engine, params={"proteins": tuple(proteins)})
    else:
        df_ppi = pd.DataFrame(columns=["proteinA_uniprot", "proteinB_uniprot", "experimental_system",
                                       "experimental_system_type", "pubmed_id"])

    # Group variants and interactions by UniProt entry
    grouped = {}
    for _, row in df.iterrows():
        uid = row["uniprot"]
        if uid not in grouped:
            # Add interactions for this protein
            interactions_list = []
            ppi_rows = df_ppi[(df_ppi["proteinA_uniprot"] == uid) | (df_ppi["proteinB_uniprot"] == uid)]
            for _, ppi in ppi_rows.iterrows():
                partner = ppi["proteinB_uniprot"] if ppi["proteinA_uniprot"] == uid else ppi["proteinA_uniprot"]
                interactions_list.append({
                    "partner": partner,
                    "experimental_system": ppi["experimental_system"],
                    "experimental_system_type": ppi["experimental_system_type"],
                    "pubmed_id": ppi["pubmed_id"]
                })

            grouped[uid] = {
                "uniprot": uid,
                "gene_names": row["gene_names"],
                "length": row["length"],
                "variants": [],
                "interactions": interactions_list
            }

        desc = (row["mutation_desc_aa"] or "").lower()
        if "silent" in desc or "synonymous" in desc:
            mutation_type = "silent"
            color = "#999999"
        elif "missense" in desc:
            mutation_type = "missense"
            color = "#e8dc03"
        elif "nonsense" in desc:
            mutation_type = "nonsense"
            color = "#ff9900"
        elif "frameshift" in desc:
            mutation_type = "frameshift"
            color = "#6600ff"
        else:
            mutation_type = "other"
            color = "#00cc99"

        if not show_silent and mutation_type == "silent":
            continue

        if pd.notnull(row["aa_mut_start"]):
            grouped[uid]["variants"].append({
                "pos": int(row["aa_mut_start"]),
                "mutation": row["mutation_aa"],
                "type_aa": row["mutation_desc_aa"],
                "mutation_type": mutation_type,
                "color": color
            })

    results = list(grouped.values())

    # Calculate stacking levels using percentages (responsive)
    for protein in results:
        protein_length = protein["length"] or 1
        levels = []  # (pct_position, level)

        for v in sorted(protein["variants"], key=lambda x: x["pos"]):
            pct_pos = v["pos"] / protein_length * 100.0
            level = 0

            # 0.6% ≈ 11 px on a ~1860px bar
            while any(abs(pct_pos - p) < 0.6 and lvl == level for p, lvl in levels):
                level += 1

            levels.append((pct_pos, level))
            v["pct_pos"] = pct_pos
            v["level"] = level

        protein["max_level"] = max((v["level"] for v in protein["variants"]), default=0)

    return render_template("results.html", results=results, query=query, show_silent=show_silent)


if __name__ == "__main__":
    app.run(debug=True)
