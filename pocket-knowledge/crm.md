# Expertise CRM (HubSpot) — appris par Pocket

- Volumes typiques (juin 2026) : ~278k contacts, ~155k companies. Lead ≈ 61 %, MQL ≈ 28 %.
- `lifecyclestage` = propriété clé pour segmenter. Industry sur **companies** = `industry_emalist`.
- Le token Pocket n'a pas le scope deals (403) — auditer deals via UI ou élargir le token.
- ICP : CA 10–500 M€, >50 employés, CFO/DAF, BE+FR, multi-entités.

<!-- L'agent ajoute ici ses apprentissages durables (datés, concis, dédupliqués). -->
- (2026-07-06) Répartition par SDR = propriété hubspot_owner_id sur contacts. La recherche HubSpot cap à 100/page → paginer via paging.next.after pour agréger (ex: 969 SQL). Résoudre les owner_id via /crm/v3/owners?archived=false ET archived=true : les gros buckets 'owner <id>' non résolus sont souvent des SDR PARTIS (archivés) → leads orphelins à réassigner. Juillet 2026 : 969 SQL, dont ~40% sur owners inactifs.
- (2026-07-10) (2026-07-10) Audit propriétés : fill rate = POST /crm/v3/objects/<t>/search avec HAS_PROPERTY, limit=1 → total (fiable >10k). Inventaire = GET /crm/v3/properties/<t>. Faits clés : internal_industry N'EXISTE PLUS sur contacts (playbooks obsolètes) → industrie = companies/industry_emalist (74%). Contacts: phone 20%, country 37%, numemployees ~1% (mort). Companies: multi-entités 17,6% (critère ICP le + vide), vat 8%, 3 props CA concurrentes (turnover/annualrevenue/turnover_category ~50%). Koalify: 4957 companies à doublons (2419 primary). Zym morte, hs_email_hard_bounce_reason=0 (emailing hors HubSpot). Rapport: pocket-data/outputs/audit-proprietes-hubspot-2026-07-10.md
- (2026-07-10) Data model structure groupes (audit 2026-07-10) : hiérarchie native Parent/Child company quasi inutilisée (890 filiales/516 mères sur 155k), 0 custom object. multiple_legal_entities_ = enum 'Yes'/'No' (PAS true/false — un filtre EQ true rend 0) : 16019 Yes. Paire sites (entities/number_of_entities) distincte de la paire entités légales. Pas de prop SIREN/BCE ; vat 8,3% = seul pivot registre. Koalify : des doublons peuvent être des sociétés sœurs d'un groupe — vérifier avant merge.
