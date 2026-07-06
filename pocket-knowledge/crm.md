# Expertise CRM (HubSpot) — appris par Pocket

- Volumes typiques (juin 2026) : ~278k contacts, ~155k companies. Lead ≈ 61 %, MQL ≈ 28 %.
- `lifecyclestage` = propriété clé pour segmenter. Industry sur **companies** = `industry_emalist`.
- Le token Pocket n'a pas le scope deals (403) — auditer deals via UI ou élargir le token.
- ICP : CA 10–500 M€, >50 employés, CFO/DAF, BE+FR, multi-entités.

<!-- L'agent ajoute ici ses apprentissages durables (datés, concis, dédupliqués). -->
- (2026-07-06) Répartition par SDR = propriété hubspot_owner_id sur contacts. La recherche HubSpot cap à 100/page → paginer via paging.next.after pour agréger (ex: 969 SQL). Résoudre les owner_id via /crm/v3/owners?archived=false ET archived=true : les gros buckets 'owner <id>' non résolus sont souvent des SDR PARTIS (archivés) → leads orphelins à réassigner. Juillet 2026 : 969 SQL, dont ~40% sur owners inactifs.
