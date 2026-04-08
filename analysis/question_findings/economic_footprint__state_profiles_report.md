# Economic Footprint: State Profiles

**TLDR:** Every state has essentially the same average AI task exposure (~36.1%), because exposure is a function of occupational task structure, not geography. What varies across states is the sector composition of their affected workforce — and that variation is real, meaningful, and clusters into five recognizable economic types. The clustering captures the structure of state economies better than it captures AI risk per se.

---

## Why State-Level Exposure Doesn't Vary

This is worth stating directly because it's counterintuitive. If you look at average pct_tasks_affected by state, every state comes back at approximately 36.1%. That's not a data error — it's how the measure works. Task exposure is computed at the occupation level using national datasets, then workers in each occupation are the same exposure level regardless of where they live. A software developer in Utah has the same AI exposure as a software developer in Massachusetts.

What does vary by state is: how many workers are in high-exposure vs. low-exposure occupations. A state with a lot of technology workers has a lot of workers in high-exposure occupations. A state with a lot of agricultural workers has many workers in low-exposure occupations. But the *average* across all workers tends to smooth out to roughly the same number because the national occupational mix isn't that different from most states' mixes.

The meaningful state variation is in sector composition — the share of each state's affected workforce that works in each major sector. That's what the clustering captures.

![State Economic Cluster Map](../questions/economic_footprint/state_profiles/figures/state_cluster_map.png)

---

## Five State Clusters

**Cluster 1 — Tech and Sun Belt metros** (AZ, CA, CO, FL, GA, MD, NC, TX, UT, VA, WA):
These states have the highest shares of Computer and Mathematical workers (~9.5%) and Sales-related workers (~9.5%) in their AI-affected workforce, plus strong Business and Financial Operations shares (~13.6%). This is the profile of tech-heavy knowledge economies: California, Texas, Washington, Colorado, Virginia. The Business/Finance share reflects both the large professional services industry in states like Maryland and Virginia (federal contractor ecosystem) and the corporate headquarters concentration in Texas and California.

**Cluster 2 — Diversified industrial and northeastern states** (AK, CT, DE, IL, MA, ME, MI, MN, MO, NH, NJ, NY, OH, OR, PA, RI, TN, VT, WI, WV):
The largest cluster by member count. These states have the highest healthcare shares (~12.4%) and more balanced sector mixes. They look like the traditional economy of the industrial Midwest and Northeast — manufacturing, healthcare, education, and services in rough proportion. The elevated healthcare share reflects both aging populations and the concentration of major medical centers and systems in states like New York, Ohio, Pennsylvania, and Illinois.

**Cluster 3 — DC alone**:
Washington DC is its own cluster and it's not close to any other state. Its Business and Financial Operations share is 24.8% — more than double any other state. Its Computer and Mathematical share is 21.2% — again roughly double. This reflects the federal government and contractor ecosystem: an economy built on policy work, analysis, IT contracting, and professional services. No other geography in the country has a comparable sector mix.

**Cluster 4 — Rural and inland states** (AL, AR, IA, ID, IN, KS, KY, LA, MS, MT, ND, NE, OK, SC, SD, WY):
These states have the highest Office/Administrative Support shares (~14.7%), the highest Food Preparation shares (~8.6%), and the highest Production shares (~2.85%). They also have the highest Transportation shares (~3.2%). This is the profile of agricultural, extraction, and light manufacturing economies. The high administrative share makes sense — administrative overhead exists in every industry, and in states without large knowledge-economy sectors, it represents a larger fraction of the exposed workforce.

**Cluster 5 — Tourism and service economies** (GU, HI, NM, NV, PR, VI):
These are geographies built on hospitality, tourism, and services. They show the highest Office/Administrative shares among all clusters (~16.1%) and elevated Protective Services (~3.65%), which likely reflects casino security (Nevada), military bases (Guam, Hawaii), and public safety roles. The Personal Care and Service share is also elevated. The exposed workforce here is more service-sector concentrated than any other cluster, which actually means more volatility — these are sectors where AI and automation have historically had uneven effects.

![Sector Composition by Cluster](../questions/economic_footprint/state_profiles/figures/cluster_heatmap.png)

---

## What the Cluster Structure Tells Us

The five clusters roughly correspond to five recognizable U.S. economic types: tech-heavy knowledge economies, diversified industrial states, the federal government hub, rural/agricultural states, and tourism-driven economies. AI doesn't change this typology — it maps onto it.

The implication is that AI's economic footprint will play out differently in each cluster, not because the average exposure differs, but because the *type* of work being exposed differs. In Cluster 1 states, the exposed work is concentrated in high-wage, high-productivity roles — Computer/Math workers at $100k+ average wages. Displacement or augmentation there has large wage implications per worker, but those workers have more resources and labor market options. In Cluster 4 states, the exposed work is more concentrated in lower-wage administrative and service roles. The absolute wage implications per worker are smaller, but the workers are more vulnerable.

The DC cluster (Cluster 3) is an interesting edge case. The federal government and contractor ecosystem has extremely high exposure — business and financial analysis, IT work, policy research — and extremely low market discipline. Firms there can't easily downsize the way private sector firms can. AI exposure in DC is probably less likely to result in headcount reduction in the near term, but the efficiency implications for government services and procurement are significant.

---

## A Note on What This Analysis Can't Resolve

The clustering methodology — k-means on sector-composition shares — finds natural groupings but doesn't rank them by risk. Cluster 4 might look lower-risk because its average exposure is no higher than anywhere else. But the *type* of risk may be worse: lower-wage workers in declining sectors in states with less economic cushion.

A richer state-level picture would incorporate state-level unemployment rates, regional wage trends, and actual AI adoption data at the firm level. What this analysis provides is a structural map of where different kinds of AI-exposed work are concentrated. That's a starting point, not a complete risk assessment.

The fact that exposure doesn't vary by state is itself worth documenting clearly. It means state-level policy responses to AI disruption should be calibrated to sector composition, not to some notion of "high-exposure states" vs. "low-exposure states." The challenge is distributed across the economy.
